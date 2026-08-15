<?php

namespace Yolol100\ElementorJsonLab;

defined( 'ABSPATH' ) || exit;

final class Widget_Inventory {
	public static function collect(): array {
		if ( ! did_action( 'elementor/loaded' ) || ! class_exists( '\\Elementor\\Plugin' ) ) {
			throw new \RuntimeException( 'Elementor is not loaded.' );
		}

		$elementor = \Elementor\Plugin::instance();
		$widgets   = $elementor->widgets_manager->get_widget_types();
		$inventory = array();

		foreach ( $widgets as $name => $widget ) {
			if ( ! is_object( $widget ) ) {
				continue;
			}

			$controls = array();
			if ( method_exists( $widget, 'get_controls' ) ) {
				foreach ( $widget->get_controls() as $control_name => $control ) {
					if ( ! is_array( $control ) ) {
						continue;
					}

					$responsive_devices = array();
					if (
						isset( $control['responsive'] )
						&& is_array( $control['responsive'] )
						&& isset( $control['responsive']['devices'] )
						&& is_array( $control['responsive']['devices'] )
					) {
						$responsive_devices = array_values(
							array_filter(
								array_map( 'strval', $control['responsive']['devices'] ),
								static function ( string $device ): bool {
									return '' !== $device;
								}
							)
						);
					}

					$controls[] = array(
						'name'               => (string) $control_name,
						'type'               => isset( $control['type'] ) && is_scalar( $control['type'] ) ? (string) $control['type'] : null,
						'responsive'         => ! empty( $control['responsive'] ) || ! empty( $control['is_responsive'] ),
						'responsive_devices' => $responsive_devices,
						'dynamic_active'     => ! empty( $control['dynamic']['active'] ),
					);
				}
			}

			usort(
				$controls,
				static function ( array $left, array $right ): int {
					return strcmp( $left['name'], $right['name'] );
				}
			);

			$owner = self::detect_owner( $widget );

			$inventory[ (string) $name ] = array(
				'name'        => method_exists( $widget, 'get_name' ) ? (string) $widget->get_name() : (string) $name,
				'title'       => method_exists( $widget, 'get_title' ) ? wp_strip_all_tags( (string) $widget->get_title() ) : (string) $name,
				'class'       => get_class( $widget ),
				'owner'       => $owner['owner'],
				'plugin_slug' => $owner['plugin_slug'],
				'categories'  => method_exists( $widget, 'get_categories' ) ? array_values( array_map( 'strval', (array) $widget->get_categories() ) ) : array(),
				'controls'    => $controls,
			);
		}

		ksort( $inventory );

		return array(
			'schema_version' => '1.1',
			'generated_at'   => gmdate( 'c' ),
			'environment'    => array(
				'wordpress'          => get_bloginfo( 'version' ),
				'php'                => PHP_VERSION,
				'elementor'          => defined( 'ELEMENTOR_VERSION' ) ? ELEMENTOR_VERSION : null,
				'elementor_pro'      => defined( 'ELEMENTOR_PRO_VERSION' ) ? ELEMENTOR_PRO_VERSION : null,
				'theme'              => wp_get_theme()->get( 'Name' ),
				'theme_version'      => wp_get_theme()->get( 'Version' ),
				'active_plugins'     => self::active_plugins(),
				'active_devices'     => self::active_devices( $elementor ),
				'active_breakpoints' => self::active_breakpoints( $elementor ),
			),
			'widgets'        => $inventory,
		);
	}

	private static function active_devices( object $elementor ): array {
		if (
			! isset( $elementor->breakpoints )
			|| ! is_object( $elementor->breakpoints )
			|| ! method_exists( $elementor->breakpoints, 'get_active_devices_list' )
		) {
			return array();
		}

		try {
			$devices = $elementor->breakpoints->get_active_devices_list(
				array(
					'add_desktop'   => true,
					'desktop_first' => true,
				)
			);
		} catch ( \Throwable $exception ) {
			return array();
		}

		return array_values(
			array_filter(
				array_map( 'strval', is_array( $devices ) ? $devices : array() ),
				static function ( string $device ): bool {
					return '' !== $device;
				}
			)
		);
	}

	private static function active_breakpoints( object $elementor ): array {
		if (
			! isset( $elementor->breakpoints )
			|| ! is_object( $elementor->breakpoints )
			|| ! method_exists( $elementor->breakpoints, 'get_active_breakpoints' )
		) {
			return array();
		}

		try {
			$breakpoints = $elementor->breakpoints->get_active_breakpoints();
		} catch ( \Throwable $exception ) {
			return array();
		}

		$result = array();

		foreach ( is_array( $breakpoints ) ? $breakpoints : array() as $name => $breakpoint ) {
			if ( ! is_object( $breakpoint ) ) {
				continue;
			}

			$result[ (string) $name ] = array(
				'label'     => method_exists( $breakpoint, 'get_label' ) ? (string) $breakpoint->get_label() : (string) $name,
				'value'     => method_exists( $breakpoint, 'get_value' ) ? (int) $breakpoint->get_value() : null,
				'direction' => method_exists( $breakpoint, 'get_direction' ) ? (string) $breakpoint->get_direction() : null,
			);
		}

		return $result;
	}

	private static function detect_owner( object $widget ): array {
		try {
			$reflection = new \ReflectionClass( $widget );
			$file       = $reflection->getFileName();
		} catch ( \ReflectionException $exception ) {
			$file = false;
		}

		if ( ! $file ) {
			return array(
				'owner'       => 'unknown',
				'plugin_slug' => null,
			);
		}

		$plugin_dir = wp_normalize_path( WP_PLUGIN_DIR );
		$file_path  = wp_normalize_path( $file );

		if ( 0 !== strpos( $file_path, $plugin_dir . '/' ) ) {
			return array(
				'owner'       => 'unknown',
				'plugin_slug' => null,
			);
		}

		$relative    = ltrim( substr( $file_path, strlen( $plugin_dir ) ), '/' );
		$parts       = explode( '/', $relative );
		$plugin_slug = sanitize_key( $parts[0] ?? '' );

		if ( 'elementor' === $plugin_slug ) {
			$owner = 'elementor-core';
		} elseif ( 'elementor-pro' === $plugin_slug ) {
			$owner = 'elementor-pro';
		} elseif ( '' !== $plugin_slug ) {
			$owner = 'third-party';
		} else {
			$owner = 'unknown';
		}

		return array(
			'owner'       => $owner,
			'plugin_slug' => $plugin_slug ?: null,
		);
	}

	private static function active_plugins(): array {
		if ( ! function_exists( 'get_plugins' ) ) {
			require_once ABSPATH . 'wp-admin/includes/plugin.php';
		}

		$all_plugins = get_plugins();
		$active      = (array) get_option( 'active_plugins', array() );
		$result      = array();

		foreach ( $active as $basename ) {
			$data = $all_plugins[ $basename ] ?? array();
			$result[] = array(
				'basename' => (string) $basename,
				'name'     => isset( $data['Name'] ) ? wp_strip_all_tags( (string) $data['Name'] ) : (string) $basename,
				'version'  => isset( $data['Version'] ) ? (string) $data['Version'] : null,
			);
		}

		usort(
			$result,
			static function ( array $left, array $right ): int {
				return strcmp( $left['basename'], $right['basename'] );
			}
		);

		return $result;
	}
}
