<?php

defined( 'ABSPATH' ) || exit;

use Elementor\Modules\GlobalClasses\Global_Classes_Repository;
use Elementor\Modules\Variables\PropTypes\Color_Variable_Prop_Type;
use Elementor\Modules\Variables\Storage\Entities\Variable;
use Elementor\Modules\Variables\Storage\Variables_Repository;

if ( ! class_exists( '\\Elementor\\Plugin' ) ) {
	throw new RuntimeException( 'Elementor is not loaded.' );
}

$kit = \Elementor\Plugin::$instance->kits_manager->get_active_kit();
if ( ! $kit ) {
	throw new RuntimeException( 'No active Elementor kit was found.' );
}

$runtime_dir = WP_PLUGIN_DIR . '/elementor-json-lab/.runtime/native-contract';
if ( ! wp_mkdir_p( $runtime_dir ) ) {
	throw new RuntimeException( 'Could not create native contract runtime directory.' );
}

$variable_id = 'e-gv-ejlfixture';
$class_id    = 'e-gc-ejlfixture';

$variables_repository = new Variables_Repository( $kit );
$variables            = $variables_repository->load();

try {
	$variables->find_or_fail( $variable_id );
} catch ( Throwable $exception ) {
	$variable = Variable::create_new(
		[
			'id'         => $variable_id,
			'type'       => Color_Variable_Prop_Type::get_key(),
			'label'      => 'ejlPrimary',
			'value'      => '#2463EB',
			'order'      => $variables->get_next_order(),
			'sync_to_v3' => false,
		]
	);
	$variable->validate();
	$variables->add_variable( $variable );
	if ( false === $variables_repository->save( $variables ) ) {
		throw new RuntimeException( 'Could not save the V4 variable fixture.' );
	}
}

$classes_repository = Global_Classes_Repository::make( $kit );
$existing_class     = $classes_repository->get( $class_id );
if ( null === $existing_class ) {
	$classes_repository->put(
		[
			$class_id => [
				'label'    => 'EJLFixture',
				'type'     => 'class',
				'variants' => [],
			],
		],
		[ $class_id ]
	);
}

$variable_state = ( new Variables_Repository( $kit ) )->load()->serialize();
$class_state    = Global_Classes_Repository::make( $kit )->get( $class_id );
if ( null === $class_state || ! isset( $variable_state['data'][ $variable_id ] ) ) {
	throw new RuntimeException( 'V4 design-system fixture readback failed.' );
}

$state = [
	'variable_id' => $variable_id,
	'class_id'    => $class_id,
	'variables'   => $variable_state,
	'class'       => $class_state,
];
$json = wp_json_encode( $state, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES );
if ( false === $json || false === file_put_contents( $runtime_dir . '/v4-fixture-state.json', $json . PHP_EOL ) ) {
	throw new RuntimeException( 'Could not write V4 fixture state.' );
}

WP_CLI::success( 'Native V4 Variable and Global Class fixture created and read back.' );
