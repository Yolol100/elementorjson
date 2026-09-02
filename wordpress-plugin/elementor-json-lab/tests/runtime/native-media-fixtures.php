<?php

defined( 'ABSPATH' ) || exit;

if ( ! class_exists( '\\Elementor\\Plugin' ) ) {
	throw new RuntimeException( 'Elementor is not loaded.' );
}

$runtime_dir = WP_PLUGIN_DIR . '/elementor-json-lab/.runtime/native-contract';
if ( ! wp_mkdir_p( $runtime_dir ) ) {
	throw new RuntimeException( 'Could not create native contract runtime directory.' );
}

require_once ABSPATH . 'wp-admin/includes/image.php';

$png = base64_decode( 'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAD0lEQVR42mNk+M9QzwAEYgH9JmHqGQAAAABJRU5ErkJggg==', true );
if ( false === $png ) {
	throw new RuntimeException( 'Could not decode fixture image.' );
}

$media = [];
for ( $index = 1; $index <= 3; ++$index ) {
	$filename = sprintf( 'ejl-native-media-%d.png', $index );
	$upload   = wp_upload_bits( $filename, null, $png );
	if ( ! empty( $upload['error'] ) ) {
		throw new RuntimeException( 'Could not create media fixture: ' . $upload['error'] );
	}

	$attachment_id = wp_insert_attachment(
		[
			'post_mime_type' => 'image/png',
			'post_title'     => sprintf( 'EJL Native Media %d', $index ),
			'post_status'    => 'inherit',
		],
		$upload['file']
	);
	if ( is_wp_error( $attachment_id ) || ! $attachment_id ) {
		throw new RuntimeException( 'Could not insert media fixture attachment.' );
	}

	$metadata = wp_generate_attachment_metadata( (int) $attachment_id, $upload['file'] );
	wp_update_attachment_metadata( (int) $attachment_id, $metadata );
	$url = wp_get_attachment_url( (int) $attachment_id );
	if ( ! is_string( $url ) || '' === $url ) {
		throw new RuntimeException( 'Could not resolve media fixture URL.' );
	}

	$media[] = [
		'id'  => (int) $attachment_id,
		'url' => $url,
	];
}

$template = [
	'title'         => 'EJL Native Media Control Contract',
	'type'          => 'page',
	'version'       => '0.4',
	'page_settings' => [],
	'content'       => [
		[
			'id'       => 'media001',
			'elType'   => 'container',
			'isInner'  => false,
			'settings' => [
				'content_width' => 'full',
			],
			'elements' => [
				[
					'id'         => 'media002',
					'elType'     => 'widget',
					'widgetType' => 'image',
					'isInner'    => false,
					'settings'   => [
						'image'      => $media[0],
						'image_size' => 'full',
					],
					'elements'   => [],
				],
				[
					'id'       => 'media003',
					'elType'   => 'container',
					'isInner'  => false,
					'settings' => [
						'background_background' => 'classic',
						'background_image'      => $media[1],
						'background_position'   => 'center center',
						'background_repeat'     => 'no-repeat',
						'background_size'       => 'cover',
						'min_height'            => [ 'unit' => 'px', 'size' => 120, 'sizes' => [] ],
					],
					'elements' => [],
				],
				[
					'id'         => 'media004',
					'elType'     => 'widget',
					'widgetType' => 'image-gallery',
					'isInner'    => false,
					'settings'   => [
						'wp_gallery'              => $media,
						'thumbnail_size'          => 'full',
						'gallery_columns'         => 3,
						'gallery_display_caption' => 'none',
						'gallery_link'            => 'none',
					],
					'elements'   => [],
				],
			],
		],
	],
];

$template_path = $runtime_dir . '/media-controls-source.json';
$state_path    = $runtime_dir . '/media-fixture-state.json';
$template_json = wp_json_encode( $template, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
$state_json    = wp_json_encode( [ 'media' => $media ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );

if ( false === $template_json || false === file_put_contents( $template_path, $template_json . PHP_EOL ) ) {
	throw new RuntimeException( 'Could not write native media source fixture.' );
}
if ( false === $state_json || false === file_put_contents( $state_path, $state_json . PHP_EOL ) ) {
	throw new RuntimeException( 'Could not write native media fixture state.' );
}

WP_CLI::success( 'Native media fixture written with three live WordPress attachments.' );
