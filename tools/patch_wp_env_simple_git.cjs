#!/usr/bin/env node
'use strict';

// Compatibility bridge for the pinned @wordpress/env 11.17.0 source.
// It still invokes the removed simple-git v3 CommonJS default function,
// whereas our audited simple-git 4.0.2 exposes a named simpleGit function.
// Fail closed on unexpected versions or source changes; never patch anything
// outside this repository's disposable node_modules installation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const OLD = "const SimpleGit = require( 'simple-git' );";
const NEW = "const { simpleGit: SimpleGit } = require( 'simple-git' );";
const INVOCATION = "const git = SimpleGit( { progress: progressHandler } );";

function patchSource(source) {
  if (typeof source !== 'string') throw new Error('Expected JavaScript source');
  const oldCount = source.split(OLD).length - 1;
  const newCount = source.split(NEW).length - 1;
  const invocationCount = source.split(INVOCATION).length - 1;
  if (newCount === 1 && oldCount === 0 && invocationCount === 1) {
    return { source, changed: false };
  }
  if (oldCount !== 1 || newCount !== 0 || invocationCount !== 1) {
    throw new Error('Unsupported @wordpress/env simple-git API source; refusing to patch');
  }
  return { source: source.replace(OLD, NEW), changed: true };
}

function selfTest() {
  const fixture = ['module.exports = {};', OLD, INVOCATION].join('\n');
  const patched = patchSource(fixture);
  assert.equal(patched.changed, true);
  assert.equal(patched.source.includes(OLD), false);
  assert.equal(patched.source.includes(NEW), true);
  assert.deepEqual(patchSource(patched.source), { source: patched.source, changed: false });
  for (const bad of [
    'module.exports = {};',
    fixture.replace(OLD, OLD + '\n' + OLD),
    fixture.replace(INVOCATION, 'const git = null;'),
    fixture.replace(OLD, NEW + '\n' + OLD),
  ]) {
    assert.throws(() => patchSource(bad), /refusing to patch/);
  }
  console.log('PASS: six pinned wp-env v11 / simple-git v4 patch scenarios');
}

function main() {
  if (process.argv[2] === '--self-test') {
    selfTest();
    return;
  }
  if (process.argv.length !== 2) throw new Error('Unexpected arguments');
  const root = path.resolve(__dirname, '..');
  const modulesRoot = path.join(root, 'node_modules');
  const installedVersion = (pkg) =>
    JSON.parse(fs.readFileSync(path.join(modulesRoot, ...pkg.split('/'), 'package.json'), 'utf8')).version;

  if (installedVersion('@wordpress/env') !== '11.17.0' || installedVersion('simple-git') !== '4.0.2') {
    throw new Error('Installed package versions differ from pinned compatibility contract');
  }
  const paths = [
    ['lib', 'download-sources.js'],
    ['lib', 'runtime', 'docker', 'download-wp-phpunit.js'],
  ];
  for (const parts of paths) {
    const file = path.join(modulesRoot, '@wordpress', 'env', ...parts);
    const actual = fs.realpathSync(file);
    if (!actual.startsWith(modulesRoot + path.sep)) throw new Error('Unsafe module file path');
    const before = fs.readFileSync(actual, 'utf8');
    const patched = patchSource(before);
    if (patched.changed) fs.writeFileSync(actual, patched.source, 'utf8');
    if (patchSource(fs.readFileSync(actual, 'utf8')).changed) throw new Error('Patch readback failed');
  }
  console.log('Verified both pinned wp-env 11.17.0 git integrations with simple-git 4.0.2');
}

module.exports = { patchSource, selfTest };
if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error('Pinned wp-env compatibility error:', error.message);
    process.exitCode = 1;
  }
}
