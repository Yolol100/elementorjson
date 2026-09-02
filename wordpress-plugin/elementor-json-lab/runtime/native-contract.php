<?php

use Yolol100\ElementorJsonLab\Native_Contract_Fixtures;

defined( 'ABSPATH' ) || exit;

require_once dirname( __DIR__ ) . '/includes/class-native-contract-fixtures.php';

$operation = isset( $args[0] ) ? (string) $args[0] : '';
$profile = isset( $args[1] ) ? (string) $args[1] : '';
$output = isset( $args[2] ) ? (string) $args[2] : '';

try {
	switch ( $operation ) {
		case 'reset':
			$result = Native_Contract_Fixtures::reset();
			break;
		case 'seed':
			$result = Native_Contract_Fixtures::seed( $profile );
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
				$repository->save( $collection );
				$result = Native_Contract_Fixtures::snapshot();
			}
			break;
		case 'export':
			$result = Native_Contract_Fixtures::export_kit( $profile, $output );
			break;
		case 'snapshot':
			$result = Native_Contract_Fixtures::snapshot();
			break;
		case 'media':
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
			break;
		default:
			throw new RuntimeException( 'Operation must be reset, seed, export, snapshot or media.' );
	}

	if ( ! in_array( $operation, array( 'export', 'media' ), true ) && '' !== $output ) {
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
