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

		$json = wp_json_encode( $inventory, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
		if ( false === $json ) {
			\WP_CLI::error( 'Could not encode the widget inventory.' );
			return;
		}

		if ( ! empty( $assoc_args['output'] ) ) {
			$path = (string) $assoc_args['output'];
			$dir  = dirname( $path );

			if ( ! is_dir( $dir ) && ! wp_mkdir_p( $dir ) ) {
				\WP_CLI::error( 'Could not create the output directory.' );
				return;
			}

			if ( false === file_put_contents( $path, $json . PHP_EOL ) ) {
				\WP_CLI::error( 'Could not write the widget inventory.' );
				return;
			}

			\WP_CLI::success( sprintf( 'Inventory written to %s', $path ) );
			return;
		}

		\WP_CLI::line( $json );
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
		);

		if ( ! empty( $assoc_args['output'] ) ) {
			$output = (string) $assoc_args['output'];
			$dir    = dirname( $output );
			if ( ! is_dir( $dir ) && ! wp_mkdir_p( $dir ) ) {
				\WP_CLI::error( 'Could not create the render manifest directory.' );
				return;
			}

			$json = wp_json_encode( $manifest, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
			if ( false === $json || false === file_put_contents( $output, $json . PHP_EOL ) ) {
				\WP_CLI::error( 'Could not write the render manifest.' );
				return;
			}
		}

		\WP_CLI::success( sprintf( 'Rendered %s at %s', basename( $template_path ), $url ) );
	}
}
