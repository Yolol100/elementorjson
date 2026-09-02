<?php

namespace Yolol100\ElementorJsonLab;

defined( 'ABSPATH' ) || exit;

final class Widget_Inventory {
	public static function collect(): array {
		if ( ! did_action( 'elementor/loaded' ) || ! class_exists( '\\Elementor\\Plugin' ) ) {
			throw new \RuntimeException( 'Elementor is not loaded.' );
		}

		$elementor = \Elementor\Plugin::instance();
		$warnings = array();
		$atomic = Atomic_Capabilities::collect( $elementor, $warnings );

		return array(
			'schema_version'      => '1.1',
			'generated_at'        => gmdate( 'c' ),
			'environment'         => array(
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
			'widgets'             => self::collect_widgets( $elementor, $warnings ),
			'elements'            => self::collect_elements( $elementor, $warnings ),
			'document_types'      => self::collect_document_types( $elementor, $warnings ),
			'dynamic_tags'        => self::collect_dynamic_tags( $elementor, $warnings ),
			'experiments'         => $atomic['experiments'],
			'atomic_style_schema' => $atomic['atomic_style_schema'],
			'atomic_dynamic_tags' => $atomic['atomic_dynamic_tags'],
			'global_classes'      => $atomic['global_classes'],
			'variables'           => $atomic['variables'],
			'components'          => $atomic['components'],
			'interactions'        => $atomic['interactions'],
			'warnings'            => array_values( array_unique( $warnings ) ),
		);
	}

	private static function collect_widgets( object $elementor, array &$warnings ): array {
		if ( ! isset( $elementor->widgets_manager ) || ! method_exists( $elementor->widgets_manager, 'get_widget_types' ) ) {
			return array();
		}

		try {
			$widgets = (array) $elementor->widgets_manager->get_widget_types();
		} catch ( \Throwable $exception ) {
			$warnings[] = 'widgets_inventory_failed';
			return array();
		}

		$result = array();
		foreach ( $widgets as $name => $widget ) {
			if ( ! is_object( $widget ) ) {
				continue;
			}
			try {
				$result[ (string) $name ] = self::component_record( $widget, (string) $name, $warnings );
			} catch ( \Throwable $exception ) {
				$warnings[] = 'widget_skipped:' . sanitize_key( (string) $name );
			}
		}
		ksort( $result );
		return $result;
	}

	private static function collect_elements( object $elementor, array &$warnings ): array {
		if ( ! isset( $elementor->elements_manager ) || ! method_exists( $elementor->elements_manager, 'get_element_types' ) ) {
			return array();
		}

		try {
			$elements = (array) $elementor->elements_manager->get_element_types();
		} catch ( \Throwable $exception ) {
			$warnings[] = 'elements_inventory_failed';
			return array();
		}

		$result = array();
		foreach ( $elements as $name => $element ) {
			if ( ! is_object( $element ) ) {
				continue;
			}
			try {
				$result[ (string) $name ] = self::component_record( $element, (string) $name, $warnings );
			} catch ( \Throwable $exception ) {
				$warnings[] = 'element_skipped:' . sanitize_key( (string) $name );
			}
		}
		ksort( $result );
		return $result;
	}

	private static function collect_document_types( object $elementor, array &$warnings ): array {
		if ( ! isset( $elementor->documents ) || ! method_exists( $elementor->documents, 'get_document_types' ) ) {
			return array();
		}

		try {
			$types = (array) $elementor->documents->get_document_types();
		} catch ( \Throwable $exception ) {
			$warnings[] = 'document_types_inventory_failed';
			return array();
		}

		$result = array();
		foreach ( $types as $type => $class_name ) {
			if ( ! is_string( $class_name ) || ! class_exists( $class_name ) ) {
				continue;
			}
			try {
				$properties = method_exists( $class_name, 'get_properties' ) ? (array) $class_name::get_properties() : array();
				$result[ (string) $type ] = array(
					'class'           => $class_name,
					'title'           => method_exists( $class_name, 'get_title' ) ? wp_strip_all_tags( (string) $class_name::get_title() ) : (string) $type,
					'plural_title'    => method_exists( $class_name, 'get_plural_title' ) ? wp_strip_all_tags( (string) $class_name::get_plural_title() ) : null,
					'cpt'             => isset( $properties['cpt'] ) ? array_values( array_map( 'strval', (array) $properties['cpt'] ) ) : array(),
					'show_in_library' => isset( $properties['show_in_library'] ) ? (bool) $properties['show_in_library'] : null,
					'register_type'   => isset( $properties['register_type'] ) ? (bool) $properties['register_type'] : null,
					'is_editable'     => isset( $properties['is_editable'] ) ? (bool) $properties['is_editable'] : null,
				);
			} catch ( \Throwable $exception ) {
				$warnings[] = 'document_type_skipped:' . sanitize_key( (string) $type );
			}
		}
		ksort( $result );
		return $result;
	}

	private static function collect_dynamic_tags( object $elementor, array &$warnings ): array {
		if ( ! isset( $elementor->dynamic_tags ) || ! method_exists( $elementor->dynamic_tags, 'get_tags' ) ) {
			return array();
		}

		try {
			$tags = $elementor->dynamic_tags->get_tags();
		} catch ( \Throwable $exception ) {
			$warnings[] = 'dynamic_tags_inventory_failed';
			return array();
		}

		$result = array();
		foreach ( (array) $tags as $name => $tag_info ) {
			$tag = is_array( $tag_info ) && isset( $tag_info['instance'] ) && is_object( $tag_info['instance'] )
				? $tag_info['instance']
				: null;
			if ( ! $tag ) {
				continue;
			}

			try {
				$owner = self::detect_owner( $tag );
				$result[ (string) $name ] = array(
					'name'        => method_exists( $tag, 'get_name' ) ? (string) $tag->get_name() : (string) $name,
					'title'       => method_exists( $tag, 'get_title' ) ? wp_strip_all_tags( (string) $tag->get_title() ) : (string) $name,
					'class'       => get_class( $tag ),
					'owner'       => $owner['owner'],
					'plugin_slug' => $owner['plugin_slug'],
					'group'       => method_exists( $tag, 'get_group' ) && is_scalar( $tag->get_group() ) ? (string) $tag->get_group() : null,
					'categories'  => method_exists( $tag, 'get_categories' ) ? array_values( array_map( 'strval', (array) $tag->get_categories() ) ) : array(),
					'controls'    => self::collect_controls( $tag, $warnings ),
				);
			} catch ( \Throwable $exception ) {
				$warnings[] = 'dynamic_tag_skipped:' . sanitize_key( (string) $name );
			}
		}
		ksort( $result );
		return $result;
	}

	private static function component_record( object $component, string $fallback_name, array &$warnings ): array {
		$owner = self::detect_owner( $component );
		$record = array(
			'name'        => method_exists( $component, 'get_name' ) ? (string) $component->get_name() : $fallback_name,
			'title'       => method_exists( $component, 'get_title' ) ? wp_strip_all_tags( (string) $component->get_title() ) : $fallback_name,
			'class'       => get_class( $component ),
			'owner'       => $owner['owner'],
			'plugin_slug' => $owner['plugin_slug'],
			'categories'  => method_exists( $component, 'get_categories' ) ? array_values( array_map( 'strval', (array) $component->get_categories() ) ) : array(),
			'controls'    => self::collect_controls( $component, $warnings ),
		);
		return array_merge( $record, Atomic_Capabilities::describe_component( $component, $warnings ) );
	}

	private static function collect_controls( object $component, array &$warnings ): array {
		if ( ! method_exists( $component, 'get_controls' ) ) {
			return array();
		}

		try {
			$raw_controls = (array) $component->get_controls();
		} catch ( \Throwable $exception ) {
			$warnings[] = 'controls_inventory_failed:' . sanitize_key( get_class( $component ) );
			return array();
		}

		$controls = array();
		foreach ( $raw_controls as $control_name => $control ) {
			if ( ! is_array( $control ) ) {
				continue;
			}

			$responsive_devices = array();
			if ( isset( $control['responsive']['devices'] ) && is_array( $control['responsive']['devices'] ) ) {
				$responsive_devices = array_values( array_filter( array_map( 'strval', $control['responsive']['devices'] ) ) );
			}

			$record = array(
				'name'               => (string) $control_name,
				'type'               => isset( $control['type'] ) && is_scalar( $control['type'] ) ? (string) $control['type'] : null,
				'responsive'         => ! empty( $control['responsive'] ) || ! empty( $control['is_responsive'] ),
				'responsive_devices' => $responsive_devices,
				'dynamic_active'     => ! empty( $control['dynamic']['active'] ),
			);

			if ( 'submit_actions' === (string) $control_name && isset( $control['options'] ) && is_array( $control['options'] ) ) {
				$keys = array_values( array_filter( array_map( 'strval', array_keys( $control['options'] ) ) ) );
				$record['choice_keys'] = array_slice( $keys, 0, 100 );
			}

			$controls[] = $record;
		}

		usort( $controls, static function ( array $left, array $right ): int {
			return strcmp( $left['name'], $right['name'] );
		} );
		return $controls;
	}

	private static function active_devices( object $elementor ): array {
		if ( ! isset( $elementor->breakpoints ) || ! is_object( $elementor->breakpoints ) || ! method_exists( $elementor->breakpoints, 'get_active_devices_list' ) ) {
			return array();
		}
		try {
			$devices = $elementor->breakpoints->get_active_devices_list( array( 'add_desktop' => true, 'desktop_first' => true ) );
		} catch ( \Throwable $exception ) {
			return array();
		}
		return array_values( array_filter( array_map( 'strval', is_array( $devices ) ? $devices : array() ) ) );
	}

	private static function active_breakpoints( object $elementor ): array {
		if ( ! isset( $elementor->breakpoints ) || ! is_object( $elementor->breakpoints ) || ! method_exists( $elementor->breakpoints, 'get_active_breakpoints' ) ) {
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
		ksort( $result );
		return $result;
	}

	private static function detect_owner( object $component ): array {
		try {
			$reflection = new \ReflectionClass( $component );
			$file = $reflection->getFileName();
		} catch ( \ReflectionException $exception ) {
			$file = false;
		}
		if ( ! $file ) {
			return array( 'owner' => 'unknown', 'plugin_slug' => null );
		}
		$plugin_dir = wp_normalize_path( WP_PLUGIN_DIR );
		$file_path = wp_normalize_path( $file );
		if ( 0 !== strpos( $file_path, $plugin_dir . '/' ) ) {
			return array( 'owner' => 'unknown', 'plugin_slug' => null );
		}
		$relative = ltrim( substr( $file_path, strlen( $plugin_dir ) ), '/' );
		$parts = explode( '/', $relative );
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
		return array( 'owner' => $owner, 'plugin_slug' => $plugin_slug ?: null );
	}

	private static function active_plugins(): array {
		if ( ! function_exists( 'get_plugins' ) ) {
			require_once ABSPATH . 'wp-admin/includes/plugin.php';
		}
		$all_plugins = get_plugins();
		$active = (array) get_option( 'active_plugins', array() );
		$result = array();
		foreach ( $active as $basename ) {
			$data = $all_plugins[ $basename ] ?? array();
			$result[] = array(
				'basename' => (string) $basename,
				'name'     => isset( $data['Name'] ) ? wp_strip_all_tags( (string) $data['Name'] ) : (string) $basename,
				'version'  => isset( $data['Version'] ) ? (string) $data['Version'] : null,
			);
		}
		usort( $result, static function ( array $left, array $right ): int {
			return strcmp( $left['basename'], $right['basename'] );
		} );
		return $result;
	}
}
