<?php

namespace Yolol100\ElementorJsonLab;

defined( 'ABSPATH' ) || exit;

final class CLI_Command {
	public function inventory( array $args, array $assoc_args ): void {
		try {
			$inventory = Widget_Inventory::collect();
		} catch ( \RuntimeException $exception ) {
			\WP_CLI::error( $exception->getMessage() );
			return;
		}
		$this->write_json_or_stdout( $inventory, $assoc_args['output'] ?? null, 'Inventory' );
	}

	/**
	 * Reopen an officially imported Elementor Library document, save it through Elementor and export its stored data.
	 *
	 * Import itself must be performed with Elementor's official `wp elementor library import` CLI command.
	 *
	 * ## OPTIONS
	 * <post-id>
	 * : Imported elementor_library post ID.
	 * --output=<path>
	 * : Roundtrip JSON destination.
	 */
	public function roundtrip( array $args, array $assoc_args ): void {
		$post_id = isset( $args[0] ) ? absint( $args[0] ) : 0;
		$output = isset( $assoc_args['output'] ) ? (string) $assoc_args['output'] : '';
		if ( ! $post_id || '' === $output ) {
			\WP_CLI::error( 'roundtrip requires a Library post ID and --output.' );
			return;
		}
		$this->export_roundtrip( $post_id, $output );
		\WP_CLI::success( sprintf( 'Roundtrip saved and exported Library template %d.', $post_id ) );
	}

	/**
	 * Render Elementor JSON into an isolated Canvas page for frontend QA.
	 *
	 * This is a render harness, not import proof. Official import + roundtrip must run first.
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
		if ( ! is_array( $data ) || JSON_ERROR_NONE !== json_last_error() || ! is_array( $data['content'] ?? null ) ) {
			\WP_CLI::error( 'Template must be valid JSON with a top-level content array.' );
			return;
		}

		$content = $data['content'];
		$filename = pathinfo( $template_path, PATHINFO_FILENAME );
		$slug = isset( $assoc_args['slug'] ) ? sanitize_title( (string) $assoc_args['slug'] ) : sanitize_title( $filename );
		$title = isset( $assoc_args['title'] ) ? sanitize_text_field( (string) $assoc_args['title'] ) : sanitize_text_field( (string) ( $data['title'] ?? $filename ) );
		if ( '' === $slug ) {
			\WP_CLI::error( 'Could not derive a valid page slug.' );
			return;
		}

		$existing = get_page_by_path( $slug, OBJECT, 'page' );
		$postarr = array(
			'post_title'   => $title ?: $slug,
			'post_name'    => $slug,
			'post_type'    => 'page',
			'post_status'  => 'publish',
			'post_content' => '',
		);
		if ( $existing instanceof \WP_Post ) {
			$postarr['ID'] = $existing->ID;
			$post_id = wp_update_post( wp_slash( $postarr ), true );
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

		$url = get_permalink( $post_id );
		$manifest = array(
			'post_id'       => (int) $post_id,
			'slug'          => $slug,
			'url'           => $url,
			'page_template' => $page_template,
			'source'        => basename( $template_path ),
		);
		if ( ! empty( $assoc_args['output'] ) ) {
			$this->write_json_file( (string) $assoc_args['output'], $manifest, 'Render manifest' );
		}
		\WP_CLI::success( sprintf( 'Rendered %s at %s', basename( $template_path ), $url ) );
	}

	private function export_roundtrip( int $post_id, string $output ): void {
		if ( 'elementor_library' !== get_post_type( $post_id ) || ! class_exists( '\\Elementor\\Plugin' ) ) {
			\WP_CLI::error( 'Roundtrip requires a valid imported elementor_library document and Elementor.' );
			return;
		}
		$elementor = \Elementor\Plugin::instance();
		$document = isset( $elementor->documents ) ? $elementor->documents->get( $post_id, false ) : false;
		if ( ! is_object( $document ) || ! method_exists( $document, 'get_elements_data' ) || ! method_exists( $document, 'get_settings' ) || ! method_exists( $document, 'save' ) ) {
			\WP_CLI::error( 'Elementor could not reopen the imported Library document.' );
			return;
		}

		$elements = $document->get_elements_data();
		$settings = $document->get_settings();
		if ( ! is_array( $elements ) || ! is_array( $settings ) ) {
			\WP_CLI::error( 'Imported document returned invalid elements/settings data.' );
			return;
		}
		try {
			$save_result = $document->save( array( 'elements' => $elements, 'settings' => $settings ) );
		} catch ( \Throwable $exception ) {
			\WP_CLI::error( 'Elementor save failed: ' . $exception->getMessage() );
			return;
		}
		if ( is_wp_error( $save_result ) ) {
			\WP_CLI::error( 'Elementor save failed: ' . $save_result->get_error_message() );
			return;
		}

		$document = $elementor->documents->get( $post_id, false );
		$elements = $document->get_elements_data();
		$settings = $document->get_settings();
		if ( ! is_array( $elements ) || ! is_array( $settings ) ) {
			\WP_CLI::error( 'Elementor could not read the document after save.' );
			return;
		}
		$post = get_post( $post_id );
		$template_type = (string) get_post_meta( $post_id, '_elementor_template_type', true );
		if ( '' === $template_type ) {
			$template_type = 'page';
		}
		$payload = array(
			'title'         => $post instanceof \WP_Post ? $post->post_title : 'Elementor template',
			'type'          => $template_type,
			'version'       => '0.4',
			'page_settings' => empty( $settings ) ? array() : $settings,
			'content'       => $elements,
		);
		$this->write_json_file( $output, $payload, 'Roundtrip export' );
	}

	private function write_json_or_stdout( array $payload, $output, string $label ): void {
		if ( ! empty( $output ) ) {
			$this->write_json_file( (string) $output, $payload, $label );
			\WP_CLI::success( sprintf( '%s written to %s', $label, (string) $output ) );
			return;
		}
		$json = wp_json_encode( $payload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
		if ( false === $json ) {
			\WP_CLI::error( 'Could not encode JSON.' );
			return;
		}
		\WP_CLI::line( $json );
	}

	private function write_json_file( string $path, array $payload, string $label ): void {
		$dir = dirname( $path );
		if ( ! is_dir( $dir ) && ! wp_mkdir_p( $dir ) ) {
			\WP_CLI::error( sprintf( '%s directory could not be created.', $label ) );
			return;
		}
		$json = wp_json_encode( $payload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
		if ( false === $json || false === file_put_contents( $path, $json . PHP_EOL ) ) {
			\WP_CLI::error( sprintf( '%s could not be written.', $label ) );
		}
	}
}
