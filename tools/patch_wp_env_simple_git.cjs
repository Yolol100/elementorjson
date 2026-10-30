#!/usr/bin/env node
'use strict';

// Compatibility bridge for pinned @wordpress/env 11.17.0 and 12.0.0.
// v11 needs its legacy CommonJS simple-git call patched within node_modules.
// Official v12 ships the native simpleGit v4 API; verify rather than patch it.
// Fail closed on unexpected versions or source changes; never patch anything
// outside this repository's disposable node_modules installation.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const OLD = "const SimpleGit = require( 'simple-git' );";
const NEW = "const { simpleGit: SimpleGit } = require( 'simple-git' );";
const INVOCATION = "const git = SimpleGit( { progress: progressHandler } );";
const NATIVE_IMPORT = "const { simpleGit } = require( 'simple-git' );";
const NATIVE_INVOCATION = "const git = simpleGit( { progress: progressHandler } );";

function verifyNativeV12Source(source) {
  if (typeof source !== 'string' ||
      source.split(NATIVE_IMPORT).length !== 2 ||
      source.split(NATIVE_INVOCATION).length !== 2 ||
      source.includes(OLD) || source.includes(NEW)) {
    throw new Error('Unsupported native @wordpress/env v12 simple-git source; refusing to patch');
  }
}

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
  const native = ['module.exports = {};', NATIVE_IMPORT, NATIVE_INVOCATION].join('\n');
  assert.doesNotThrow(() => verifyNativeV12Source(native));
  for (const bad of [fixture, native.replace(NATIVE_IMPORT, ''), native.replace(NATIVE_IMPORT, NATIVE_IMPORT + '\n' + NATIVE_IMPORT), native.replace(NATIVE_INVOCATION, 'const git = null;')]) {
    assert.throws(() => verifyNativeV12Source(bad), /refusing to patch/);
  }
  console.log('PASS: legacy v11 patch and native v12 verification fixtures');
}

function main() {
  if (process.argv[2] === '--self-test') {
    selfTest();
    return;
  }
  if (process.argv.length !== 2) throw new Error('Unexpected arguments');
  selfTest();
  const root = path.resolve(__dirname, '..');
  const modulesRoot = path.join(root, 'node_modules');
  const installedVersion = (pkg) =>
    JSON.parse(fs.readFileSync(path.join(modulesRoot, ...pkg.split('/'), 'package.json'), 'utf8')).version;

  const envVersion = installedVersion('@wordpress/env');
  if (!['11.17.0', '12.0.0'].includes(envVersion) || installedVersion('simple-git') !== '4.0.2') {
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
    if (envVersion === '12.0.0') {
      verifyNativeV12Source(before);
      continue;
    }
    const patched = patchSource(before);
    if (patched.changed) fs.writeFileSync(actual, patched.source, 'utf8');
    if (patchSource(fs.readFileSync(actual, 'utf8')).changed) throw new Error('Patch readback failed');
  }
  console.log('Verified pinned wp-env ' + envVersion + ' integrations with simple-git 4.0.2');
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
