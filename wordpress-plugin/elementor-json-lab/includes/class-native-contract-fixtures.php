<?php

namespace Yolol100\ElementorJsonLab;

use Elementor\Modules\GlobalClasses\Global_Classes_Repository;
use Elementor\Modules\Variables\Storage\Variables_Collection;
use Elementor\Modules\Variables\Storage\Variables_Repository;
use Elementor\Plugin;
use RuntimeException;

defined( 'ABSPATH' ) || exit;

final class Native_Contract_Fixtures {
	public const SCHEMA_VERSION = '1.0';
	private const FIXTURE_META_KEY = '_ejl_native_contract_fixture';

	public static function reset(): array {
		$kit = self::active_kit();
		self::clear_v3( $kit );
		self::clear_v4( $kit );
		self::remove_fixture_media();

		return self::snapshot();
	}

	public static function seed( string $profile ): array {
		$profile = self::assert_profile( $profile );
		$kit = self::active_kit();
		self::clear_v3( $kit );
		self::clear_v4( $kit );

		if ( 'v3' === $profile || 'mixed' === $profile ) {
			self::seed_v3( $kit );
		}

		if ( 'v4' === $profile || 'mixed' === $profile ) {
			self::seed_v4( $kit );
		}

		return self::snapshot();
	}

	public static function export_kit( string $profile, string $output ): array {
		$profile = self::assert_profile( $profile );
		$module = Plugin::instance()->app->get_component( 'import-export' );
		if ( ! $module || ! method_exists( $module, 'export_kit' ) ) {
			throw new RuntimeException( 'Elementor native import/export component is unavailable.' );
		}

		$settings = array(
			'include' => array( 'settings' ),
			'customization' => array(
				'settings' => self::customization( $profile ),
			),
		);

		$result = $module->export_kit( $settings );
		$source = isset( $result['file_name'] ) ? (string) $result['file_name'] : '';
		if ( '' === $source || ! is_file( $source ) ) {
			throw new RuntimeException( 'Elementor did not produce a native kit archive.' );
		}

		$dir = dirname( $output );
		if ( ! is_dir( $dir ) && ! wp_mkdir_p( $dir ) ) {
			throw new RuntimeException( 'Could not create native kit output directory.' );
		}
		if ( is_file( $output ) && ! unlink( $output ) ) {
			throw new RuntimeException( 'Could not replace an existing native kit fixture.' );
		}
		if ( ! rename( $source, $output ) ) {
			throw new RuntimeException( 'Could not move the native Elementor kit archive.' );
		}

		return array(
			'schema_version' => self::SCHEMA_VERSION,
			'profile' => $profile,
			'path' => $output,
			'sha256' => hash_file( 'sha256', $output ),
			'bytes' => filesize( $output ),
			'elementor' => defined( 'ELEMENTOR_VERSION' ) ? ELEMENTOR_VERSION : '',
			'wordpress' => get_bloginfo( 'version' ),
		);
	}

	public static function snapshot(): array {
		$kit = self::active_kit();
		$kit_data = $kit->get_export_data();
		$settings = isset( $kit_data['settings'] ) && is_array( $kit_data['settings'] ) ? $kit_data['settings'] : array();
		$v3_keys = array(
			'custom_colors',
			'custom_typography',
			'body_color',
			'body_typography_typography',
			'body_typography_font_family',
			'body_typography_font_size',
			'container_width',
			'space_between_widgets',
			'button_background_color',
			'button_text_color',
			'button_border_radius',
		);
		$v3 = array();
		foreach ( $v3_keys as $key ) {
			if ( array_key_exists( $key, $settings ) ) {
				$v3[ $key ] = $settings[ $key ];
			}
		}
		ksort( $v3, SORT_STRING );

		$classes = array();
		if ( class_exists( Global_Classes_Repository::class ) ) {
			$repo = Global_Classes_Repository::make( $kit );
			foreach ( $repo->get_order() as $id ) {
				$item = $repo->get( (string) $id );
				if ( is_array( $item ) ) {
					$classes[ (string) $id ] = $item;
				}
			}
		}
		ksort( $classes, SORT_STRING );

		$variables = array();
		if ( class_exists( Variables_Repository::class ) ) {
			$repo = new Variables_Repository( $kit );
			$serialized = $repo->load()->serialize( true );
			$variables = isset( $serialized['data'] ) && is_array( $serialized['data'] ) ? $serialized['data'] : array();
			foreach ( $variables as &$variable ) {
				if ( is_array( $variable ) ) {
					unset( $variable['created_at'], $variable['updated_at'], $variable['deleted_at'] );
				}
			}
			unset( $variable );
		}
		ksort( $variables, SORT_STRING );

		return array(
			'schema_version' => self::SCHEMA_VERSION,
			'environment' => array(
				'wordpress' => get_bloginfo( 'version' ),
				'elementor' => defined( 'ELEMENTOR_VERSION' ) ? ELEMENTOR_VERSION : '',
			),
			'v3' => $v3,
			'v4' => array(
				'classes' => $classes,
				'variables' => $variables,
			),
		);
	}

	public static function create_media_templates( string $output_dir ): array {
		self::remove_fixture_media();
		$attachments = array(
			self::create_png_attachment( 'ejl-contract-a.png', 'EJL Contract A' ),
			self::create_png_attachment( 'ejl-contract-b.png', 'EJL Contract B' ),
			self::create_png_attachment( 'ejl-contract-c.png', 'EJL Contract C' ),
		);
		if ( count( $attachments ) !== 3 ) {
			throw new RuntimeException( 'Could not create three media contract attachments.' );
		}

		if ( ! is_dir( $output_dir ) && ! wp_mkdir_p( $output_dir ) ) {
			throw new RuntimeException( 'Could not create the media contract output directory.' );
		}

		$image = self::document(
			'EJL Native Image Control',
			array(
				self::container(
					'a1b2c3d4',
					array(
						self::widget(
							'b1c2d3e4',
							'image',
							array(
								'image' => self::media_value( $attachments[0] ),
								'image_size' => 'full',
							)
						),
					)
				),
			)
		);

		$background = self::document(
			'EJL Native Background Control',
			array(
				self::container(
					'c1d2e3f4',
					array(),
					array(
						'background_background' => 'classic',
						'background_image' => self::media_value( $attachments[1] ),
						'background_position' => 'center center',
						'background_repeat' => 'no-repeat',
						'background_size' => 'cover',
					)
				),
			)
		);

		$gallery_items = array_map( array( self::class, 'media_value' ), $attachments );
		$gallery = self::document(
			'EJL Native Gallery Control',
			array(
				self::container(
					'd1e2f3a4',
					array(
						self::widget(
							'e1f2a3b4',
							'image-gallery',
							array(
								'gallery' => $gallery_items,
								'gallery_columns' => '3',
								'gallery_link' => 'none',
								'image_size' => 'full',
							)
						),
					)
				),
			)
		);

		$files = array(
			'image-control.json' => $image,
			'background-control.json' => $background,
			'gallery-control.json' => $gallery,
		);
		foreach ( $files as $name => $document ) {
			self::write_json_file( trailingslashit( $output_dir ) . $name, $document );
		}

		return array(
			'schema_version' => self::SCHEMA_VERSION,
			'attachments' => $attachments,
			'files' => array_keys( $files ),
		);
	}

	private static function customization( string $profile ): array {
		$v3 = 'v3' === $profile || 'mixed' === $profile;
		$v4 = 'v4' === $profile || 'mixed' === $profile;
		return array(
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
	}

	private static function seed_v3( $kit ): void {
		$kit->update_settings(
			array(
				'custom_colors' => array(
					array( '_id' => 'ejlprimary', 'title' => 'EJL Primary', 'color' => '#1F5F8B' ),
					array( '_id' => 'ejlaccent', 'title' => 'EJL Accent', 'color' => '#D97706' ),
				),
				'custom_typography' => array(
					array(
						'_id' => 'ejlbody',
						'title' => 'EJL Body',
						'typography_typography' => 'custom',
						'typography_font_family' => 'Arial',
						'typography_font_weight' => '400',
					),
				),
				'body_color' => '#1F2937',
				'body_typography_typography' => 'custom',
				'body_typography_font_family' => 'Arial',
				'body_typography_font_size' => array( 'unit' => 'px', 'size' => 16, 'sizes' => array() ),
				'container_width' => array( 'unit' => 'px', 'size' => 1180, 'sizes' => array() ),
				'space_between_widgets' => array( 'unit' => 'px', 'size' => 20, 'sizes' => array() ),
				'button_background_color' => '#1F5F8B',
				'button_text_color' => '#FFFFFF',
				'button_border_radius' => array( 'unit' => 'px', 'top' => 8, 'right' => 8, 'bottom' => 8, 'left' => 8, 'isLinked' => true ),
			)
		);
	}

	private static function clear_v3( $kit ): void {
		$kit->update_settings(
			array(
				'custom_colors' => array(),
				'custom_typography' => array(),
				'body_color' => '',
				'body_typography_typography' => '',
				'body_typography_font_family' => '',
				'body_typography_font_size' => array(),
				'container_width' => array(),
				'space_between_widgets' => array(),
				'button_background_color' => '',
				'button_text_color' => '',
				'button_border_radius' => array(),
			)
		);
	}

	private static function seed_v4( $kit ): void {
		self::assert_v4_runtime();
		$classes = array(
			'g-ejl-card' => array(
				'id' => 'g-ejl-card',
				'type' => 'class',
				'label' => 'EJL Card',
				'variants' => array(
					array(
						'meta' => array( 'breakpoint' => 'desktop', 'state' => null ),
						'props' => array(
							'color' => array( '$$type' => 'color', 'value' => '#1F2937' ),
							'padding' => array( '$$type' => 'size', 'value' => array( 'size' => 24, 'unit' => 'px' ) ),
						),
					),
				),
			),
		);
		Global_Classes_Repository::make( $kit )->put( $classes, array( 'g-ejl-card' ) );

		$collection = Variables_Collection::hydrate(
			array(
				'data' => array(
					'e-gv-ejl-primary' => array(
						'type' => 'global-color-variable',
						'label' => 'ejl-primary',
						'value' => '#1F5F8B',
						'order' => 1,
						'sync_to_v3' => false,
						'created_at' => '2026-09-02 00:00:00',
						'updated_at' => '2026-09-02 00:00:00',
					),
				),
				'watermark' => 0,
				'version' => 1,
			)
		);
		( new Variables_Repository( $kit ) )->save( $collection );
	}

	private static function clear_v4( $kit ): void {
		if ( class_exists( Global_Classes_Repository::class ) ) {
			Global_Classes_Repository::make( $kit )->put( array(), array() );
		}
		if ( class_exists( Variables_Repository::class ) && class_exists( Variables_Collection::class ) ) {
			( new Variables_Repository( $kit ) )->save( Variables_Collection::default() );
		}
	}

	private static function assert_v4_runtime(): void {
		$classes = array(
			'\\Elementor\\Modules\\AtomicWidgets\\Module',
			'\\Elementor\\Modules\\GlobalClasses\\Module',
			'\\Elementor\\Modules\\Variables\\Module',
			Global_Classes_Repository::class,
			Variables_Repository::class,
			Variables_Collection::class,
		);
		foreach ( $classes as $class ) {
			if ( ! class_exists( $class ) ) {
				throw new RuntimeException( 'Required Elementor V4 class is unavailable: ' . $class );
			}
		}

		$experiments = Plugin::instance()->experiments;
		$features = array(
			\Elementor\Modules\AtomicWidgets\Module::EXPERIMENT_NAME,
			\Elementor\Modules\GlobalClasses\Module::NAME,
			\Elementor\Modules\Variables\Module::EXPERIMENT_NAME,
		);
		foreach ( $features as $feature ) {
			if ( ! $experiments->is_feature_active( $feature ) ) {
				throw new RuntimeException( 'Required Elementor V4 feature is inactive: ' . $feature );
			}
		}
	}

	private static function active_kit() {
		if ( ! class_exists( Plugin::class ) ) {
			throw new RuntimeException( 'Elementor is not active.' );
		}
		$kit = Plugin::instance()->kits_manager->get_active_kit();
		if ( ! $kit ) {
			throw new RuntimeException( 'No active Elementor Kit is available.' );
		}
		return $kit;
	}

	private static function assert_profile( string $profile ): string {
		$profile = strtolower( trim( $profile ) );
		if ( ! in_array( $profile, array( 'v3', 'v4', 'mixed' ), true ) ) {
			throw new RuntimeException( 'Profile must be one of: v3, v4, mixed.' );
		}
		return $profile;
	}

	private static function create_png_attachment( string $filename, string $title ): array {
		$png = base64_decode( 'iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAFElEQVR42mNk+M/wn4GBgYGJAQoAHgQCAQ7R1YQAAAAASUVORK5CYII=', true );
		if ( false === $png ) {
			throw new RuntimeException( 'Could not decode the media fixture PNG.' );
		}
		$upload = wp_upload_bits( $filename, null, $png );
		if ( ! empty( $upload['error'] ) ) {
			throw new RuntimeException( 'Could not create media fixture: ' . $upload['error'] );
		}
		$attachment_id = wp_insert_attachment(
			array(
				'post_mime_type' => 'image/png',
				'post_title' => $title,
				'post_status' => 'inherit',
			),
			$upload['file']
		);
		if ( is_wp_error( $attachment_id ) || ! $attachment_id ) {
			throw new RuntimeException( 'Could not create the media fixture attachment.' );
		}
		require_once ABSPATH . 'wp-admin/includes/image.php';
		$metadata = wp_generate_attachment_metadata( $attachment_id, $upload['file'] );
		if ( is_array( $metadata ) ) {
			wp_update_attachment_metadata( $attachment_id, $metadata );
		}
		update_post_meta( $attachment_id, self::FIXTURE_META_KEY, '1' );
		update_post_meta( $attachment_id, '_wp_attachment_image_alt', $title . ' alt' );
		$url = wp_get_attachment_url( $attachment_id );
		if ( ! is_string( $url ) || '' === $url ) {
			throw new RuntimeException( 'Could not resolve the media fixture URL.' );
		}
		return array( 'id' => (int) $attachment_id, 'url' => $url, 'title' => $title );
	}

	private static function remove_fixture_media(): void {
		$ids = get_posts(
			array(
				'post_type' => 'attachment',
				'post_status' => 'any',
				'posts_per_page' => -1,
				'fields' => 'ids',
				'meta_key' => self::FIXTURE_META_KEY,
				'meta_value' => '1',
			)
		);
		foreach ( $ids as $id ) {
			wp_delete_attachment( (int) $id, true );
		}
	}

	private static function media_value( array $attachment ): array {
		return array( 'id' => (int) $attachment['id'], 'url' => (string) $attachment['url'] );
	}

	private static function document( string $title, array $content ): array {
		return array(
			'title' => $title,
			'type' => 'page',
			'version' => '0.4',
			'page_settings' => array(),
			'content' => $content,
		);
	}

	private static function container( string $id, array $elements, array $settings = array() ): array {
		return array(
			'id' => $id,
			'elType' => 'container',
			'settings' => array_merge( array( 'content_width' => 'full' ), $settings ),
			'elements' => $elements,
			'isInner' => false,
		);
	}

	private static function widget( string $id, string $type, array $settings ): array {
		return array(
			'id' => $id,
			'elType' => 'widget',
			'widgetType' => $type,
			'settings' => $settings,
			'elements' => array(),
			'isInner' => false,
		);
	}

	private static function write_json_file( string $path, array $data ): void {
		$json = wp_json_encode( $data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
		if ( false === $json || false === file_put_contents( $path, $json . PHP_EOL ) ) {
			throw new RuntimeException( 'Could not write native contract JSON: ' . $path );
		}
	}
}
