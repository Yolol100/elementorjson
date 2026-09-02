<?php

use Yolol100\ElementorJsonLab\Native_Contract_Fixtures;

defined( 'ABSPATH' ) || exit;

require_once dirname( __DIR__ ) . '/includes/class-native-contract-fixtures.php';

$operation = isset( $args[0] ) ? (string) $args[0] : '';
$profile = isset( $args[1] ) ? strtolower( trim( (string) $args[1] ) ) : '';
$output = isset( $args[2] ) ? (string) $args[2] : '';

$assert_profile = static function ( string $candidate ): string {
	if ( ! in_array( $candidate, array( 'v3', 'v4', 'mixed' ), true ) ) {
		throw new RuntimeException( 'Profile must be one of: v3, v4, mixed.' );
	}
	return $candidate;
};

$customization = static function ( string $candidate, bool $for_import = false ): array {
	$v3 = in_array( $candidate, array( 'v3', 'mixed' ), true );
	$v4 = in_array( $candidate, array( 'v4', 'mixed' ), true );
	$settings = array(
		'theme' => false,
		'globalColors' => $v3,
		'globalFonts' => $v3,
		'themeStyleSettings' => $v3,
		'generalSettings' => $v3,
		'experiments' => false,
		'customCode' => false,
		'customIcons' => false,
		'customFonts' => false,
		'classes' => $v4,
		'variables' => $v4,
	);
	if ( $for_import ) {
		$settings['classesOverrideAll'] = $v4;
		$settings['variablesOverrideAll'] = $v4;
	}
	return array( 'settings' => $settings );
};

$current_import_export = static function () {
	$module = \Elementor\Plugin::instance()->app->get_component( 'import-export-customization' );
	if ( ! $module || ! method_exists( $module, 'export_kit' ) || ! method_exists( $module, 'import_kit' ) ) {
		throw new RuntimeException( 'Elementor import-export-customization is unavailable.' );
	}
	return $module;
};

$fresh_kit = static function ( string $label ): void {
	$manager = \Elementor\Plugin::instance()->kits_manager;
	if ( ! $manager || ! method_exists( $manager, 'create_new_kit' ) ) {
		throw new RuntimeException( 'Elementor Kits Manager cannot create an isolated fixture kit.' );
	}
	$kit_id = $manager->create_new_kit( $label, array(), true );
	if ( ! $kit_id || (int) $manager->get_active_id() !== (int) $kit_id ) {
		throw new RuntimeException( 'Could not activate an isolated Elementor fixture kit.' );
	}
};

try {
	switch ( $operation ) {
		case 'reset':
			$result = Native_Contract_Fixtures::reset();
			break;

		case 'seed':
			$profile = $assert_profile( $profile );
			$fresh_kit( 'EJL Native Contract ' . strtoupper( $profile ) );
			Native_Contract_Fixtures::seed( $profile );
			if ( in_array( $profile, array( 'v4', 'mixed' ), true ) ) {
				$kit = \Elementor\Plugin::instance()->kits_manager->get_active_kit();
				$repository = new \Elementor\Modules\Variables\Storage\Variables_Repository( $kit );
				$serialized = $repository->load()->serialize( true );
				$data = isset( $serialized['data'] ) && is_array( $serialized['data'] ) ? $serialized['data'] : array();
				$data['e-gv-ejl-font'] = array(
					'type' => 'global-font-variable',
					'label' => 'ejl-font',
					'value' => 'Arial',
					'order' => 2,
					'sync_to_v3' => false,
					'created_at' => '2026-09-02 00:00:00',
					'updated_at' => '2026-09-02 00:00:00',
				);
				$data['e-gv-ejl-space'] = array(
					'type' => 'global-size-variable',
					'label' => 'ejl-space',
					'value' => '1.5rem',
					'order' => 3,
					'sync_to_v3' => false,
					'created_at' => '2026-09-02 00:00:00',
					'updated_at' => '2026-09-02 00:00:00',
				);
				$collection = \Elementor\Modules\Variables\Storage\Variables_Collection::hydrate(
					array(
						'data' => $data,
						'watermark' => isset( $serialized['watermark'] ) ? (int) $serialized['watermark'] : 0,
						'version' => isset( $serialized['version'] ) ? (int) $serialized['version'] : 1,
					)
				);
				if ( false === $repository->save( $collection ) ) {
					throw new RuntimeException( 'Could not persist the V4 variable fixture.' );
				}
			}
			$result = Native_Contract_Fixtures::snapshot();
			break;

		case 'export':
			$profile = $assert_profile( $profile );
			if ( '' === $output ) {
				throw new RuntimeException( 'Native Website Template ZIP output path is required.' );
			}
			$module = $current_import_export();
			$export = $module->export_kit(
				array(
					'include' => array( 'settings' ),
					'kitInfo' => array(
						'title' => 'EJL Native ' . strtoupper( $profile ) . ' Contract',
						'description' => 'Sanitized Elementor controlled-runtime compiler contract.',
						'source' => 'local',
					),
					'customization' => $customization( $profile, false ),
				)
			);
			$source = isset( $export['file_name'] ) ? (string) $export['file_name'] : '';
			if ( '' === $source || ! is_file( $source ) ) {
				throw new RuntimeException( 'Elementor did not produce a current native Website Template ZIP.' );
			}
			$dir = dirname( $output );
			if ( ! is_dir( $dir ) && ! wp_mkdir_p( $dir ) ) {
				throw new RuntimeException( 'Could not create the native Website Template output directory.' );
			}
			if ( is_file( $output ) && ! unlink( $output ) ) {
				throw new RuntimeException( 'Could not replace the native Website Template fixture.' );
			}
			if ( ! rename( $source, $output ) ) {
				throw new RuntimeException( 'Could not move the native Website Template fixture.' );
			}
			$result = array(
				'profile' => $profile,
				'path' => $output,
				'sha256' => hash_file( 'sha256', $output ),
				'bytes' => filesize( $output ),
				'elementor' => defined( 'ELEMENTOR_VERSION' ) ? ELEMENTOR_VERSION : '',
				'wordpress' => get_bloginfo( 'version' ),
				'format' => 'import-export-customization',
			);
			break;

		case 'import':
			$profile = $assert_profile( $profile );
			if ( '' === $output || ! is_file( $output ) ) {
				throw new RuntimeException( 'Existing native Website Template ZIP path is required.' );
			}
			$fresh_kit( 'EJL Native Import Target ' . strtoupper( $profile ) );
			$module = $current_import_export();
			$result = $module->import_kit(
				$output,
				array(
					'include' => array( 'settings' ),
					'referrer' => 'local',
					'customization' => $customization( $profile, true ),
				)
			);
			break;

		case 'snapshot':
			$result = Native_Contract_Fixtures::snapshot();
			break;

		case 'media':
			if ( '' === $output ) {
				throw new RuntimeException( 'Native media contract output directory is required.' );
			}
			$result = Native_Contract_Fixtures::create_media_templates( $output );

			$gallery_path = trailingslashit( $output ) . 'gallery-control.json';
			$gallery_raw = is_readable( $gallery_path ) ? file_get_contents( $gallery_path ) : false;
			$gallery_data = false !== $gallery_raw ? json_decode( $gallery_raw, true ) : null;
			if ( ! is_array( $gallery_data ) || JSON_ERROR_NONE !== json_last_error() ) {
				throw new RuntimeException( 'Could not read generated Basic Gallery contract JSON.' );
			}
			$settings =& $gallery_data['content'][0]['elements'][0]['settings'];
			if ( ! is_array( $settings ) || ! isset( $settings['gallery'] ) || ! is_array( $settings['gallery'] ) ) {
				throw new RuntimeException( 'Generated Basic Gallery contract lacks the expected media list.' );
			}
			$settings['wp_gallery'] = $settings['gallery'];
			unset( $settings['gallery'] );
			$settings['thumbnail_size'] = 'full';
			unset( $settings['image_size'] );
			$gallery_json = wp_json_encode( $gallery_data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
			if ( false === $gallery_json || false === file_put_contents( $gallery_path, $gallery_json . PHP_EOL ) ) {
				throw new RuntimeException( 'Could not write canonical Basic Gallery contract JSON.' );
			}

			$local = \Elementor\Plugin::instance()->templates_manager->get_source( 'local' );
			if ( ! $local ) {
				throw new RuntimeException( 'Elementor local Template Library source is unavailable.' );
			}
			$reflection = new ReflectionClass( $local );
			$prepare = $reflection->getMethod( 'prepare_template_export' );
			$prepare->setAccessible( true );
			foreach ( array( 'image-control.json', 'background-control.json', 'gallery-control.json' ) as $filename ) {
				$path = trailingslashit( $output ) . $filename;
				$raw = is_readable( $path ) ? file_get_contents( $path ) : false;
				$template = false !== $raw ? json_decode( $raw, true ) : null;
				if ( ! is_array( $template ) || JSON_ERROR_NONE !== json_last_error() ) {
					throw new RuntimeException( 'Could not read generated media template: ' . $filename );
				}
				$template_id = $local->save_item(
					array(
						'title' => (string) ( $template['title'] ?? $filename ),
						'type' => (string) ( $template['type'] ?? 'page' ),
						'content' => isset( $template['content'] ) && is_array( $template['content'] ) ? $template['content'] : array(),
						'page_settings' => isset( $template['page_settings'] ) && is_array( $template['page_settings'] ) ? $template['page_settings'] : array(),
					)
				);
				if ( is_wp_error( $template_id ) || ! $template_id ) {
					throw new RuntimeException( 'Elementor could not save native media template: ' . $filename );
				}
				$file_data = $prepare->invoke( $local, (int) $template_id );
				if ( is_wp_error( $file_data ) || ! is_array( $file_data ) || empty( $file_data['content'] ) ) {
					throw new RuntimeException( 'Elementor could not export native media template: ' . $filename );
				}
				if ( false === file_put_contents( $path, (string) $file_data['content'] ) ) {
					throw new RuntimeException( 'Could not persist native media export: ' . $filename );
				}
			}
			$result['native_template_export'] = true;
			break;

		default:
			throw new RuntimeException( 'Operation must be reset, seed, export, import, snapshot or media.' );
	}

	if ( ! in_array( $operation, array( 'export', 'import', 'media' ), true ) && '' !== $output ) {
		$dir = dirname( $output );
		if ( ! is_dir( $dir ) && ! wp_mkdir_p( $dir ) ) {
			throw new RuntimeException( 'Could not create native contract output directory.' );
		}
		$json = wp_json_encode( $result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
		if ( false === $json || false === file_put_contents( $output, $json . PHP_EOL ) ) {
			throw new RuntimeException( 'Could not write native contract output.' );
		}
	}

	WP_CLI::success( 'Native contract operation completed.' );
} catch ( Throwable $error ) {
	WP_CLI::error( $error->getMessage() );
}
