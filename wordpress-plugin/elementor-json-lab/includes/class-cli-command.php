<?php

namespace Yolol100\ElementorJsonLab;

defined( 'ABSPATH' ) || exit;

final class CLI_Command {
	/**
	 * Export the registered Elementor widget and control inventory.
	 *
	 * ## OPTIONS
	 *
	 * [--output=<path>]
	 * : Write JSON to a file instead of stdout.
	 */
	public function inventory( array $args, array $assoc_args ): void {
		try {
			$inventory = Widget_Inventory::collect();
		} catch ( \RuntimeException $exception ) {
			\WP_CLI::error( $exception->getMessage() );
			return;
		}

		$this->emit_json( $inventory, isset( $assoc_args['output'] ) ? (string) $assoc_args['output'] : '' );
	}

	/**
	 * Render an Elementor export JSON file into an isolated WordPress page.
	 *
	 * ## OPTIONS
	 *
	 * <template>
	 * : Absolute path to an Elementor JSON export.
	 *
	 * [--slug=<slug>]
	 * : Page slug. Defaults to the template filename.
	 *
	 * [--title=<title>]
	 * : Page title. Defaults to the export title or filename.
	 *
	 * [--page-template=<template>]
	 * : WordPress page template. Defaults to elementor_canvas for isolated previews.
	 *
	 * [--output=<path>]
	 * : Optional JSON manifest output path.
	 */
	public function render( array $args, array $assoc_args ): void {
		$template_path = isset( $args[0] ) ? (string) $args[0] : '';
		if ( '' === $template_path || ! is_readable( $template_path ) ) {
			\WP_CLI::error( 'Template JSON file is missing or unreadable.' );
			return;
		}

		$raw = file_get_contents( $template_path );
		if ( false === $raw ) {
			\WP_CLI::error( 'Could not read the template JSON file.' );
			return;
		}

		$data = json_decode( $raw, true );
		if ( ! is_array( $data ) || JSON_ERROR_NONE !== json_last_error() ) {
			\WP_CLI::error( 'Template is not valid JSON.' );
			return;
		}

		$content = $data['content'] ?? null;
		if ( ! is_array( $content ) ) {
			\WP_CLI::error( 'Template must contain a top-level content array.' );
			return;
		}

		$filename = pathinfo( $template_path, PATHINFO_FILENAME );
		$slug     = isset( $assoc_args['slug'] ) ? sanitize_title( (string) $assoc_args['slug'] ) : sanitize_title( $filename );
		$title    = isset( $assoc_args['title'] ) ? sanitize_text_field( (string) $assoc_args['title'] ) : sanitize_text_field( (string) ( $data['title'] ?? $filename ) );

		if ( '' === $slug ) {
			\WP_CLI::error( 'Could not derive a valid page slug.' );
			return;
		}

		$existing = get_page_by_path( $slug, OBJECT, 'page' );
		$postarr  = array(
			'post_title'   => $title ?: $slug,
			'post_name'    => $slug,
			'post_type'    => 'page',
			'post_status'  => 'publish',
			'post_content' => '',
		);

		if ( $existing instanceof \WP_Post ) {
			$postarr['ID'] = $existing->ID;
			$post_id       = wp_update_post( wp_slash( $postarr ), true );
		} else {
			$post_id = wp_insert_post( wp_slash( $postarr ), true );
		}

		if ( is_wp_error( $post_id ) ) {
			\WP_CLI::error( $post_id->get_error_message() );
			return;
		}

		$encoded_content = wp_json_encode( $content );
		if ( false === $encoded_content ) {
			\WP_CLI::error( 'Could not encode Elementor content.' );
			return;
		}

		update_post_meta( $post_id, '_elementor_edit_mode', 'builder' );
		update_post_meta( $post_id, '_elementor_template_type', 'wp-page' );
		update_post_meta( $post_id, '_elementor_data', wp_slash( $encoded_content ) );
		update_post_meta( $post_id, '_elementor_version', defined( 'ELEMENTOR_VERSION' ) ? ELEMENTOR_VERSION : '' );
		update_post_meta( $post_id, '_elementor_page_settings', is_array( $data['page_settings'] ?? null ) ? $data['page_settings'] : array() );

		$page_template = isset( $assoc_args['page-template'] ) ? sanitize_key( (string) $assoc_args['page-template'] ) : 'elementor_canvas';
		if ( '' !== $page_template ) {
			update_post_meta( $post_id, '_wp_page_template', $page_template );
		}

		if ( class_exists( '\\Elementor\\Plugin' ) ) {
			$elementor = \Elementor\Plugin::instance();
			if ( isset( $elementor->files_manager ) && method_exists( $elementor->files_manager, 'clear_cache' ) ) {
				$elementor->files_manager->clear_cache();
			}
		}

		$url      = get_permalink( $post_id );
		$manifest = array(
			'post_id'       => (int) $post_id,
			'slug'          => $slug,
			'url'           => $url,
			'page_template' => $page_template,
			'source'        => basename( $template_path ),
			'mode'          => 'direct-postmeta-preview',
		);

		if ( ! empty( $assoc_args['output'] ) ) {
			$this->emit_json( $manifest, (string) $assoc_args['output'], false );
		}

		\WP_CLI::success( sprintf( 'Rendered %s at %s', basename( $template_path ), $url ) );
	}

	/**
	 * Re-export the Elementor data stored for an imported Template Library item.
	 *
	 * This command intentionally reads the post created by Elementor's official
	 * `wp elementor library import` command. It does not replace the importer; it
	 * exposes the imported data so the CI harness can perform a semantic
	 * source-versus-import roundtrip comparison.
	 *
	 * ## OPTIONS
	 *
	 * <post-id>
	 * : Imported elementor_library post ID.
	 *
	 * [--output=<path>]
	 * : Write JSON to a file instead of stdout.
	 */
	public function export_template( array $args, array $assoc_args ): void {
		$post_id = isset( $args[0] ) ? absint( $args[0] ) : 0;
		$post    = $post_id ? get_post( $post_id ) : null;
		if ( ! $post instanceof \WP_Post || 'elementor_library' !== $post->post_type ) {
			\WP_CLI::error( 'A valid imported elementor_library post ID is required.' );
			return;
		}

		$raw_content = get_post_meta( $post_id, '_elementor_data', true );
		$content     = is_string( $raw_content ) ? json_decode( $raw_content, true ) : null;
		if ( ! is_array( $content ) && is_string( $raw_content ) ) {
			$content = json_decode( wp_unslash( $raw_content ), true );
		}
		if ( ! is_array( $content ) ) {
			\WP_CLI::error( 'Imported template does not contain readable _elementor_data JSON.' );
			return;
		}

		$page_settings = get_post_meta( $post_id, '_elementor_page_settings', true );
		if ( ! is_array( $page_settings ) ) {
			$page_settings = array();
		}
		$template_type = (string) get_post_meta( $post_id, '_elementor_template_type', true );

		$document = array(
			'title'         => $post->post_title,
			'type'          => $template_type ?: 'page',
			'version'       => '0.4',
			'page_settings' => $page_settings,
			'content'       => $content,
			'_qa'           => array(
				'imported_post_id' => $post_id,
				'elementor_version' => defined( 'ELEMENTOR_VERSION' ) ? ELEMENTOR_VERSION : null,
				'source'            => 'elementor-library-import-postmeta-readback',
			),
		);

		$this->emit_json( $document, isset( $assoc_args['output'] ) ? (string) $assoc_args['output'] : '' );
	}

	private function emit_json( array $data, string $output = '', bool $success_message = true ): void {
		$json = wp_json_encode( $data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
		if ( false === $json ) {
			\WP_CLI::error( 'Could not encode JSON output.' );
			return;
		}

		if ( '' === $output ) {
			\WP_CLI::line( $json );
			return;
		}

		$dir = dirname( $output );
		if ( ! is_dir( $dir ) && ! wp_mkdir_p( $dir ) ) {
			\WP_CLI::error( 'Could not create the output directory.' );
			return;
		}
		if ( false === file_put_contents( $output, $json . PHP_EOL ) ) {
			\WP_CLI::error( 'Could not write JSON output.' );
			return;
		}
		if ( $success_message ) {
			\WP_CLI::success( sprintf( 'JSON written to %s', $output ) );
		}
	}
}
