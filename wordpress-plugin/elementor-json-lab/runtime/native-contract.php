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
			break;
		case 'export':
			$result = Native_Contract_Fixtures::export_kit( $profile, $output );
			break;
		case 'snapshot':
			$result = Native_Contract_Fixtures::snapshot();
			break;
		case 'media':
			$result = Native_Contract_Fixtures::create_media_templates( $output );
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
