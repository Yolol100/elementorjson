<?php

defined( 'ABSPATH' ) || exit;

use Elementor\Modules\GlobalClasses\Global_Classes_Repository;
use Elementor\Modules\Variables\Storage\Variables_Repository;

if ( ! class_exists( '\\Elementor\\Plugin' ) ) {
	throw new RuntimeException( 'Elementor is not loaded.' );
}

$kit = \Elementor\Plugin::$instance->kits_manager->get_active_kit();
if ( ! $kit ) {
	throw new RuntimeException( 'No active Elementor kit was found.' );
}

$class = Global_Classes_Repository::make( $kit )->get( 'e-gc-ejlfixture' );
$variables = ( new Variables_Repository( $kit ) )->load()->serialize();
$variable = $variables['data']['e-gv-ejlfixture'] ?? null;

if ( ! is_array( $class ) || 'EJLFixture' !== ( $class['label'] ?? null ) ) {
	throw new RuntimeException( 'Native kit import did not restore the expected Global Class.' );
}
if ( ! is_array( $variable ) || 'ejlPrimary' !== ( $variable['label'] ?? null ) || '#2463EB' !== ( $variable['value'] ?? null ) ) {
	throw new RuntimeException( 'Native kit import did not restore the expected Variable.' );
}

WP_CLI::success( 'Native kit import restored the V4 Variable and Global Class.' );
