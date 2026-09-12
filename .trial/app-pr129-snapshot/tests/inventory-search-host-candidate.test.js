'use strict';

const assert = require('assert');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const Builder = require('../tools/build-inventory-search-host-candidate');
const productionLock = require('../integrations/inventory-search/database-artifact.lock.json');

function hashBuffer(buffer) {
  return 'SHA256-' + crypto.createHash('sha256').update(buffer).digest('hex').toUpperCase();
}
function writeJson(file, value) { fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n'); }
function makeFixture(root) {
  const artifactDir = path.join(root, 'artifact');
  fs.mkdirSync(artifactDir, { recursive: true });
  const bundleName = 'erei-inventory-search-policy.gs';
  const manifestName = 'erei-inventory-search-policy.manifest.json';
  const bundle = Buffer.from(
    "var EREIInventorySearchPolicy = (function(){ return {policy_id:'EREI-INVENTORY-SEARCH-POLICY-V1',normalizeFilters:function(f){return f||{};},compileFilters:function(f){return {policy_id:'EREI-INVENTORY-SEARCH-POLICY-V1',filters:f||{}};},evaluateCandidate:function(){return {eligible:true};},budgetDistance:function(){return 0;},compareCandidates:function(){return 0;},rankEligible:function(x){return x||[];}};})();\n",
    'utf8'
  );
  const bundleSha = hashBuffer(bundle);
  fs.writeFileSync(path.join(artifactDir, bundleName), bundle);
  const manifest = {
    schema_version: '1.0', artifact_type: 'apps_script_inventory_search_bundle', artifact_id: 'IPASIS-TEST',
    package_name: 'erei-real-estate-decision-intelligence', package_entrypoint: null,
    source_entrypoint: 'runtime/core/InventorySearchPolicy.js', exposed_global: 'EREIInventorySearchPolicy',
    runtime_target: 'google_apps_script_v8', module_count: 2,
    source_modules: ['runtime/core/CriteriaEngine.js', 'runtime/core/InventorySearchPolicy.js'],
    external_commonjs_requires_not_bundled: [], node_module_system_required_at_runtime: false,
    package_root_only: false, deep_imports_exposed: false, bundle_sha256: bundleSha
  };
  const manifestBytes = Buffer.from(JSON.stringify(manifest, null, 2) + '\n', 'utf8');
  fs.writeFileSync(path.join(artifactDir, manifestName), manifestBytes);
  const lock = {
    schema_version: '1.0', integration_id: 'EREI-INVENTORY-SEARCH-HOST-CANDIDATE-V1',
    source: { repository: 'lijust/database', branch: 'main', commit: 'fixture', pull_request: 93, workflow_run_id: 1, artifact_id: 2, artifact_name: 'fixture', archive_digest: 'sha256:fixture' },
    inventory_bundle: {
      filename: bundleName, sha256: bundleSha, manifest_filename: manifestName, manifest_sha256: hashBuffer(manifestBytes),
      artifact_type: manifest.artifact_type, bundle_artifact_id: manifest.artifact_id,
      source_entrypoint: manifest.source_entrypoint, source_modules: manifest.source_modules,
      exposed_global: manifest.exposed_global, runtime_target: manifest.runtime_target, module_count: 2,
      external_commonjs_requires_not_bundled: [], node_module_system_required_at_runtime: false,
      package_root_only: false, deep_imports_exposed: false
    },
    policy: {
      policy_id: 'EREI-INVENTORY-SEARCH-POLICY-V1', contract_path: 'contracts/inventory-search-policy.v1.json',
      conformance_path: 'contracts/conformance/inventory-search-policy.v1.json', implementation_path: 'runtime/core/InventorySearchPolicy.js',
      criteria_engine_path: 'runtime/core/CriteriaEngine.js'
    },
    candidate: {
      build_outside_src_only: true, generated_bundle_only: true, compile_policy_once_per_search: true,
      host_alias_resolution_retained: true, host_partitioning_retained: true, host_candidate_cache_retained: true,
      host_top_k_retained: true, host_hydration_retained: true, host_quota_exposure_retained: true,
      host_snapshot_retained: true, controller_contract_unchanged: true,
      browser_surface_expanded: false, customer_visible_behavior_authorized: false
    },
    release_authority: {
      source_candidate_only: true, current_src_mutation: false, clasp_push: false, apps_script_head_mutation: false,
      script_properties_mutation: false, version_creation: false, deployment_repoint: false,
      runtime_inventory_search_cutover: false, production_promotion: false
    }
  };
  const lockPath = path.join(root, 'lock.json');
  writeJson(lockPath, lock);
  return { artifactDir, lockPath, bundleName, manifestName };
}

assert.strictEqual(productionLock.source.commit, 'ed8f8f9caf4925c2258b27b6ac130d631c9b0315');
assert.strictEqual(productionLock.source.workflow_run_id, 33962517930);
assert.strictEqual(productionLock.source.artifact_id, 9968374424);
assert.strictEqual(productionLock.source.archive_digest, 'sha256:d9b053a521d13b6417058e5af81d8a715b750e9fd30f4b6521de41f7bbe50600');
assert.strictEqual(productionLock.inventory_bundle.bundle_artifact_id, 'IPASIS-677D6CA5B6C54B09F1AF3C9A6314167B');
assert.strictEqual(productionLock.inventory_bundle.sha256, 'SHA256-677D6CA5B6C54B09F1AF3C9A6314167BF6D8782747C94A1A921A94AD8FC150ED');
assert.strictEqual(productionLock.inventory_bundle.manifest_sha256, 'SHA256-8C6D8A8E2177D201D3E576150AE15DC09BCAE0137A97AD195B13A01951A13136');
assert.strictEqual(productionLock.inventory_bundle.exposed_global, 'EREIInventorySearchPolicy');
assert.strictEqual(productionLock.candidate.compile_policy_once_per_search, true);
assert.strictEqual(productionLock.release_authority.runtime_inventory_search_cutover, false);

const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'erei-inventory-host-'));
try {
  const fixture = makeFixture(temp);
  const outputDir = path.join(temp, 'candidate');
  const evidencePath = path.join(temp, 'candidate.manifest.json');
  const srcDigestBefore = Builder.digestTree(path.join(ROOT, 'src'));
  const result = Builder.buildCandidate({ artifactDir: fixture.artifactDir, lockPath: fixture.lockPath, outputDir, evidencePath });
  const srcDigestAfter = Builder.digestTree(path.join(ROOT, 'src'));

  assert.strictEqual(srcDigestBefore, srcDigestAfter, 'current src must remain byte-identical');
  assert.strictEqual(result.evidence.current_src_mutated, false);
  assert.strictEqual(result.evidence.generated_bundle_installed, true);
  assert.strictEqual(result.evidence.deterministic_inventory_policy_primary_in_candidate, true);
  assert.strictEqual(result.evidence.policy_compiled_once_per_search, true);
  ['host_alias_resolution_retained','host_partitioning_retained','host_candidate_cache_retained','host_top_k_retained','host_hydration_retained','host_quota_exposure_retained','host_snapshot_retained'].forEach(key => assert.strictEqual(result.evidence[key], true));
  assert.strictEqual(result.evidence.runtime_cutover_authorized, false);
  assert(fs.existsSync(path.join(outputDir, '31_EREIInventorySearchPolicy.gs')));

  const candidateSearch = fs.readFileSync(path.join(outputDir, '32_SearchService.gs'), 'utf8');
  ['normalizeFilters','compileFilters','evaluateCandidate','compareCandidates'].forEach(method => assert(candidateSearch.includes('EREIInventorySearchPolicy.' + method)));
  assert(candidateSearch.includes('compiledInventorySearchPolicy_'));
  assert(!candidateSearch.includes("if(f.city&&normalizeLower_(o.city)!==normalizeLower_(f.city))return false;"));
  assert(!candidateSearch.includes("if(f.price_min!==null&&(price===null||price<f.price_min))return false;"));
  assert(!candidateSearch.includes('var cmp=function(a,b){var da=budgetDistance_(a,f)'));

  [
    'RuntimeHotPathV9.canonicalizeFilters', 'resolveHumanNames_', 'searchWindow_',
    'SearchCandidateCacheRepository.open()', 'insertTopK_', 'hydratePageV7_',
    'RegistryRepository.precheckSearchUsage', 'RegistryRepository.reserveSearchUsage',
    'queueSnapshotV9_', 'writeSnapshot_'
  ].forEach(token => assert(candidateSearch.includes(token), 'host responsibility missing: ' + token));

  const originalController = fs.readFileSync(path.join(ROOT, 'src', '50_Controller.gs'), 'utf8');
  const candidateController = fs.readFileSync(path.join(outputDir, '50_Controller.gs'), 'utf8');
  assert.strictEqual(candidateController, originalController, 'Controller must remain byte-identical');
  assert(!candidateController.includes('EREIInventorySearchPolicy'));

  fs.appendFileSync(path.join(fixture.artifactDir, fixture.bundleName), '// tamper\n');
  assert.throws(() => Builder.buildCandidate({ artifactDir: fixture.artifactDir, lockPath: fixture.lockPath, outputDir: path.join(temp, 'tampered-bundle'), evidencePath: path.join(temp, 'tampered-bundle.json') }), /bundle sha256 mismatch/);

  const fixture2 = makeFixture(path.join(temp, 'second'));
  const manifestPath = path.join(fixture2.artifactDir, fixture2.manifestName);
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  manifest.exposed_global = 'TamperedGlobal';
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
  assert.throws(() => Builder.buildCandidate({ artifactDir: fixture2.artifactDir, lockPath: fixture2.lockPath, outputDir: path.join(temp, 'tampered-manifest'), evidencePath: path.join(temp, 'tampered-manifest.json') }), /manifest sha256 mismatch/);
} finally {
  fs.rmSync(temp, { recursive: true, force: true });
}

console.log('PASS inventory-search host candidate: exact artifact lock, one-time policy compilation, portable eligibility/ranking authority, host hot-path responsibilities retained, current src immutable, tamper fail-closed');
