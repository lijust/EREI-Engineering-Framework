'use strict';

const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const PortableHostCandidateBuilder = require('../tools/lib/portable-host-candidate-builder');

function sha256Buffer(buffer) {
  return 'SHA256-' + crypto.createHash('sha256').update(buffer).digest('hex').toUpperCase();
}

function writeJson(file, value) {
  fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n', 'utf8');
}

function makeFixture(root) {
  const srcDir = path.join(root, 'src');
  const artifactDir = path.join(root, 'artifact');
  const outputDir = path.join(root, 'candidate');
  const evidencePath = path.join(root, 'candidate.manifest.json');
  fs.mkdirSync(srcDir, { recursive: true });
  fs.mkdirSync(artifactDir, { recursive: true });
  fs.writeFileSync(path.join(srcDir, '10_Base.gs'), 'const BASE = true;\n', 'utf8');

  const bundleName = 'fixture-policy.gs';
  const manifestName = 'fixture-policy.manifest.json';
  const bundle = Buffer.from(
    "var FixturePolicy = (function(){ return {evaluateCandidate:function(){return true;}};})();\n",
    'utf8'
  );
  const bundleSha = sha256Buffer(bundle);
  fs.writeFileSync(path.join(artifactDir, bundleName), bundle);
  const manifest = {
    artifact_type: 'fixture_portable_bundle',
    artifact_id: 'FIXTURE-1',
    exposed_global: 'FixturePolicy',
    runtime_target: 'google_apps_script_v8',
    bundle_sha256: bundleSha,
    source_modules: ['runtime/core/FixturePolicy.js'],
    external_commonjs_requires_not_bundled: []
  };
  const manifestBytes = Buffer.from(JSON.stringify(manifest, null, 2) + '\n', 'utf8');
  fs.writeFileSync(path.join(artifactDir, manifestName), manifestBytes);

  const lock = {
    schema_version: '1.0',
    integration_id: 'FIXTURE-HOST-CANDIDATE-V1',
    bundle: {
      filename: bundleName,
      sha256: bundleSha,
      manifest_filename: manifestName,
      manifest_sha256: sha256Buffer(manifestBytes),
      artifact_type: manifest.artifact_type,
      bundle_artifact_id: manifest.artifact_id,
      exposed_global: manifest.exposed_global,
      runtime_target: manifest.runtime_target,
      source_modules: manifest.source_modules,
      external_commonjs_requires_not_bundled: manifest.external_commonjs_requires_not_bundled
    }
  };
  const lockPath = path.join(root, 'lock.json');
  writeJson(lockPath, lock);
  return { srcDir, artifactDir, outputDir, evidencePath, lockPath, bundleName };
}

function configFor(fixture) {
  return {
    rootDir: fixture.srcDir,
    lockPath: fixture.lockPath,
    artifactDir: fixture.artifactDir,
    srcDir: fixture.srcDir,
    outputDir: fixture.outputDir,
    evidencePath: fixture.evidencePath,
    validateLock(lock) {
      assert.strictEqual(lock.integration_id, 'FIXTURE-HOST-CANDIDATE-V1');
    },
    artifact: {
      label: 'fixture portable policy',
      getSpec(lock) { return lock.bundle; },
      installFilename: '31_FixturePolicy.gs',
      manifestFields(spec) {
        return {
          artifact_type: spec.artifact_type,
          artifact_id: spec.bundle_artifact_id,
          exposed_global: spec.exposed_global,
          runtime_target: spec.runtime_target,
          bundle_sha256: spec.sha256
        };
      },
      manifestArrays(spec) {
        return {
          source_modules: spec.source_modules,
          external_commonjs_requires_not_bundled: spec.external_commonjs_requires_not_bundled
        };
      },
      requiredMethods: ['evaluateCandidate']
    },
    mutateCandidate({ outputDir }) {
      fs.appendFileSync(path.join(outputDir, '10_Base.gs'), 'const CANDIDATE_ONLY = true;\n', 'utf8');
    },
    verifyCandidate({ outputDir }) {
      const text = fs.readFileSync(path.join(outputDir, '10_Base.gs'), 'utf8');
      assert(text.includes('CANDIDATE_ONLY'));
    },
    createEvidence({ lock, verified }) {
      return {
        schema_version: '1.0',
        candidate_id: lock.integration_id,
        exposed_global: verified.spec.exposed_global,
        runtime_cutover_authorized: false
      };
    }
  };
}

const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'erei-portable-candidate-lifecycle-'));
try {
  const fixture = makeFixture(temp);
  const sourceBefore = fs.readFileSync(path.join(fixture.srcDir, '10_Base.gs'), 'utf8');
  const result = PortableHostCandidateBuilder.run(configFor(fixture));
  const sourceAfter = fs.readFileSync(path.join(fixture.srcDir, '10_Base.gs'), 'utf8');

  assert.strictEqual(sourceAfter, sourceBefore, 'public lifecycle must keep source byte-identical');
  assert(fs.existsSync(path.join(fixture.outputDir, '31_FixturePolicy.gs')), 'verified bundle must be installed into candidate');
  assert.strictEqual(result.evidence.current_src_mutated, false);
  assert.strictEqual(result.evidence.generated_bundle_installed, true);
  assert.strictEqual(result.evidence.runtime_cutover_authorized, false);
  assert.match(result.evidence.current_src_digest_before, /^SHA256-[A-F0-9]{64}$/);
  assert.strictEqual(result.evidence.current_src_digest_after, result.evidence.current_src_digest_before);
  assert.match(result.evidence.candidate_digest, /^SHA256-[A-F0-9]{64}$/);
  assert.deepStrictEqual(JSON.parse(fs.readFileSync(fixture.evidencePath, 'utf8')), result.evidence);

  const tampered = makeFixture(path.join(temp, 'tampered'));
  fs.appendFileSync(path.join(tampered.artifactDir, tampered.bundleName), '// tamper\n', 'utf8');
  assert.throws(() => PortableHostCandidateBuilder.run(configFor(tampered)), /bundle sha256 mismatch/);

  const platformLeak = makeFixture(path.join(temp, 'platform-leak'));
  fs.appendFileSync(path.join(platformLeak.artifactDir, platformLeak.bundleName), 'SpreadsheetApp.getActive();\n', 'utf8');
  const bytes = fs.readFileSync(path.join(platformLeak.artifactDir, platformLeak.bundleName));
  const lock = JSON.parse(fs.readFileSync(platformLeak.lockPath, 'utf8'));
  lock.bundle.sha256 = sha256Buffer(bytes);
  const manifestPath = path.join(platformLeak.artifactDir, 'fixture-policy.manifest.json');
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  manifest.bundle_sha256 = lock.bundle.sha256;
  writeJson(manifestPath, manifest);
  lock.bundle.manifest_sha256 = sha256Buffer(fs.readFileSync(manifestPath));
  writeJson(platformLeak.lockPath, lock);
  assert.throws(() => PortableHostCandidateBuilder.run(configFor(platformLeak)), /host\/platform dependency/);

  const sourceMutation = makeFixture(path.join(temp, 'source-mutation'));
  const mutationConfig = configFor(sourceMutation);
  mutationConfig.mutateCandidate = function mutateAndIllegallyTouchSource({ outputDir }) {
    fs.appendFileSync(path.join(outputDir, '10_Base.gs'), 'const CANDIDATE_ONLY = true;\n', 'utf8');
    fs.appendFileSync(path.join(sourceMutation.srcDir, '10_Base.gs'), 'const ILLEGAL_SOURCE_MUTATION = true;\n', 'utf8');
  };
  assert.throws(() => PortableHostCandidateBuilder.run(mutationConfig), /current src mutated/);
  assert.strictEqual(fs.existsSync(sourceMutation.evidencePath), false, 'failed source-integrity build must not emit success evidence');
} finally {
  fs.rmSync(temp, { recursive: true, force: true });
}

console.log('PASS portable host candidate builder: public lifecycle owns artifact verification, candidate copy/install, source immutability, evidence, and fail-closed safety');
