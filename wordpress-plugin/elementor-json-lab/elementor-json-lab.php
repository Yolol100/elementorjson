<?php
/**
 * Plugin Name: Elementor JSON Lab
 * Description: Exports Elementor runtime/design-system inventory and supports isolated render and official-import roundtrip QA.
 * Version: 0.2.0
 * Requires at least: 6.8
 * Requires PHP: 7.4
 * Text Domain: elementor-json-lab
 */

namespace Yolol100\ElementorJsonLab;

defined( 'ABSPATH' ) || exit;

define( 'EJL_VERSION', '0.2.0' );
define( 'EJL_FILE', __FILE__ );

require_once __DIR__ . '/includes/class-widget-inventory.php';
require_once __DIR__ . '/includes/class-cli-command.php';

if ( defined( 'WP_CLI' ) && WP_CLI ) {
	\WP_CLI::add_command( 'ejl', CLI_Command::class );
}
