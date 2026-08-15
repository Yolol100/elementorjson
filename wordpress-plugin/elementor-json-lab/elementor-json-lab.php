<?php
/**
 * Plugin Name: Elementor JSON Lab
 * Description: Exports the registered Elementor widget/control inventory and renders Elementor JSON templates for isolated QA previews.
 * Version: 0.1.0
 * Requires at least: 6.8
 * Requires PHP: 7.4
 * Text Domain: elementor-json-lab
 */

namespace Yolol100\ElementorJsonLab;

defined( 'ABSPATH' ) || exit;

define( 'EJL_VERSION', '0.1.0' );
define( 'EJL_FILE', __FILE__ );

require_once __DIR__ . '/includes/class-widget-inventory.php';
require_once __DIR__ . '/includes/class-cli-command.php';

if ( defined( 'WP_CLI' ) && WP_CLI ) {
	\WP_CLI::add_command( 'ejl', CLI_Command::class );
}
