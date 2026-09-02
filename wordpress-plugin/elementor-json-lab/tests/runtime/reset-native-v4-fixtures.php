<?php

defined( 'ABSPATH' ) || exit;

use Elementor\Modules\GlobalClasses\Global_Classes_Repository;
use Elementor\Modules\Variables\Storage\Variables_Collection;
use Elementor\Modules\Variables\Storage\Variables_Repository;

if ( ! class_exists( '\\Elementor\\Plugin' ) ) {
	throw new RuntimeException( 'Elementor is not loaded.' );
}

$kit = \Elementor\Plugin::$instance->kits_manager->get_active_kit();
if ( ! $kit ) {
	throw new RuntimeException( 'No active Elementor kit was found.' );
}

Global_Classes_Repository::make( $kit )->put( [], [] );
$variables_repository = new Variables_Repository( $kit );
if ( false === $variables_repository->save( Variables_Collection::default() ) ) {
	throw new RuntimeException( 'Could not reset V4 variables.' );
}

if ( null !== Global_Classes_Repository::make( $kit )->get( 'e-gc-ejlfixture' ) ) {
	throw new RuntimeException( 'Global Class fixture remained after reset.' );
}
if ( isset( ( new Variables_Repository( $kit ) )->load()->serialize()['data']['e-gv-ejlfixture'] ) ) {
	throw new RuntimeException( 'Variable fixture remained after reset.' );
}

WP_CLI::success( 'Native V4 fixtures reset.' );
