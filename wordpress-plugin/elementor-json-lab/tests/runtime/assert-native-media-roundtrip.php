<?php

defined( 'ABSPATH' ) || exit;

$path = WP_PLUGIN_DIR . '/elementor-json-lab/.runtime/native-contract/media-controls-roundtrip.json';
if ( ! is_readable( $path ) ) {
	throw new RuntimeException( 'Media roundtrip JSON is missing.' );
}

$data = json_decode( (string) file_get_contents( $path ), true, 512, JSON_THROW_ON_ERROR );
$image = null;
$background = null;
$gallery = null;

$walk = static function ( array $elements ) use ( &$walk, &$image, &$background, &$gallery ): void {
	foreach ( $elements as $element ) {
		if ( ! is_array( $element ) ) {
			continue;
		}
		$settings = isset( $element['settings'] ) && is_array( $element['settings'] ) ? $element['settings'] : [];
		if ( 'image' === ( $element['widgetType'] ?? '' ) && isset( $settings['image'] ) && is_array( $settings['image'] ) ) {
			$image = $settings['image'];
		}
		if ( isset( $settings['background_image']['id'], $settings['background_image']['url'] ) && '' !== (string) $settings['background_image']['id'] ) {
			$background = $settings['background_image'];
		}
		if ( 'image-gallery' === ( $element['widgetType'] ?? '' ) && isset( $settings['wp_gallery'] ) && is_array( $settings['wp_gallery'] ) ) {
			$gallery = $settings['wp_gallery'];
		}
		if ( isset( $element['elements'] ) && is_array( $element['elements'] ) ) {
			$walk( $element['elements'] );
		}
	}
};
$walk( $data['content'] ?? [] );

$assert_media = static function ( array $item, string $label ): array {
	$id = isset( $item['id'] ) ? (int) $item['id'] : 0;
	$url = isset( $item['url'] ) ? (string) $item['url'] : '';
	if ( $id <= 0 || '' === $url || ! wp_attachment_is_image( $id ) ) {
		throw new RuntimeException( $label . ' does not reference a live WordPress image attachment.' );
	}
	$live_url = wp_get_attachment_url( $id );
	if ( ! is_string( $live_url ) || $live_url !== $url ) {
		throw new RuntimeException( $label . ' id+url does not match the live WordPress attachment.' );
	}
	return [ 'id' => $id, 'url' => $url ];
};

if ( ! is_array( $image ) ) {
	throw new RuntimeException( 'Imported Image control was not found.' );
}
if ( ! is_array( $background ) ) {
	throw new RuntimeException( 'Imported Background Media control was not found.' );
}
if ( ! is_array( $gallery ) || 3 !== count( $gallery ) ) {
	throw new RuntimeException( 'Imported Basic Gallery control did not preserve three media items.' );
}

$report = [
	'image'      => $assert_media( $image, 'Image control' ),
	'background' => $assert_media( $background, 'Background control' ),
	'gallery'    => [],
];
foreach ( $gallery as $index => $item ) {
	if ( ! is_array( $item ) ) {
		throw new RuntimeException( 'Gallery item is not an object.' );
	}
	$report['gallery'][] = $assert_media( $item, 'Gallery item ' . ( $index + 1 ) );
}

$report['status'] = 'pass';
$report['import_semantics'] = 'Elementor Template Library may sideload media and rewrite attachment ids/urls; every rewritten reference must resolve to its live WordPress image.';
$json = wp_json_encode( $report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
if ( false === $json || false === file_put_contents( WP_PLUGIN_DIR . '/elementor-json-lab/.runtime/native-contract/media-controls-runtime-validation.json', $json . PHP_EOL ) ) {
	throw new RuntimeException( 'Could not write media roundtrip validation report.' );
}

WP_CLI::success( 'Imported Image, Background and Basic Gallery references resolve to live WordPress attachments.' );
