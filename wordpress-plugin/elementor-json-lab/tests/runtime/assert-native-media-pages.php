<?php

defined( 'ABSPATH' ) || exit;

$runtime_dir = WP_PLUGIN_DIR . '/elementor-json-lab/.runtime/native-contract';
$cases = [
	'ejl-native-image' => [ 'file' => '04-image-widget.json', 'mode' => 'image' ],
	'ejl-native-background' => [ 'file' => '05-background-image.json', 'mode' => 'background' ],
	'ejl-native-gallery' => [ 'file' => '06-gallery.json', 'mode' => 'gallery' ],
];
$report = [];

$assert_pair = static function ( array $pair, string $label ): array {
	$id = isset( $pair['id'] ) ? (int) $pair['id'] : 0;
	$url = isset( $pair['url'] ) ? (string) $pair['url'] : '';
	if ( $id <= 0 || '' === $url || ! wp_attachment_is_image( $id ) ) {
		throw new RuntimeException( $label . ' is not a live WordPress image attachment.' );
	}
	$live = wp_get_attachment_url( $id );
	if ( ! is_string( $live ) || $live !== $url ) {
		throw new RuntimeException( $label . ' id+url does not match WordPress readback.' );
	}
	return [ 'id' => $id, 'url' => $url ];
};

foreach ( $cases as $slug => $case ) {
	$page = get_page_by_path( $slug, OBJECT, 'page' );
	if ( ! $page instanceof WP_Post ) {
		throw new RuntimeException( 'Rendered media page is missing: ' . $slug );
	}
	$raw = get_post_meta( $page->ID, '_elementor_data', true );
	$content = is_string( $raw ) ? json_decode( $raw, true, 512, JSON_THROW_ON_ERROR ) : $raw;
	if ( ! is_array( $content ) || empty( $content[0]['elements'][0] ) ) {
		throw new RuntimeException( 'Rendered Elementor content is missing for ' . $slug );
	}
	$element = $content[0]['elements'][0];
	$settings = is_array( $element['settings'] ?? null ) ? $element['settings'] : [];
	if ( 'image' === $case['mode'] ) {
		$report['image'] = $assert_pair( $settings['image'] ?? [], 'Image control' );
	} elseif ( 'background' === $case['mode'] ) {
		$report['background'] = $assert_pair( $settings['background_image'] ?? [], 'Background Media control' );
	} else {
		$gallery = $settings['wp_gallery'] ?? null;
		if ( ! is_array( $gallery ) || 3 !== count( $gallery ) ) {
			throw new RuntimeException( 'Basic Gallery did not preserve three media items.' );
		}
		$report['gallery'] = [];
		foreach ( $gallery as $index => $item ) {
			$report['gallery'][] = $assert_pair( is_array( $item ) ? $item : [], 'Gallery item ' . ( $index + 1 ) );
		}
	}
}

$report['status'] = 'pass';
$report['semantics'] = 'Same-site Elementor save/readback preserves existing live WordPress attachment id+url references for Image, Background Media and Basic Gallery.';
$json = wp_json_encode( $report, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
if ( false === $json || false === file_put_contents( $runtime_dir . '/media-pages-readback.json', $json . PHP_EOL ) ) {
	throw new RuntimeException( 'Could not write media page readback report.' );
}
WP_CLI::success( 'Same-site Image, Background and Basic Gallery id+url readback passed.' );
