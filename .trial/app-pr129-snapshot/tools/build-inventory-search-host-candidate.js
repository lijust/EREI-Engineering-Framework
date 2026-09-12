#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const PortableHostCandidateBuilder = require('./lib/portable-host-candidate-builder');

const ROOT = path.resolve(__dirname, '..');
const DEFAULT_LOCK = path.join(ROOT, 'integrations', 'inventory-search', 'database-artifact.lock.json');
const DEFAULT_SRC = path.join(ROOT, 'src');
const DEFAULT_OUT = path.join(ROOT, 'build', 'inventory-search-host');
const DEFAULT_EVIDENCE = path.join(ROOT, 'build', 'inventory-search-host.manifest.json');

function fail(message) { throw new Error(message); }

function validateLock(lock) {
  if (lock.schema_version !== '1.0') fail('lock schema_version drift');
  if (lock.integration_id !== 'EREI-INVENTORY-SEARCH-HOST-CANDIDATE-V1') fail('lock integration id drift');
  if (!lock.source || lock.source.repository !== 'lijust/database') fail('source repository drift');
  const candidate = lock.candidate || {};
  [
    'build_outside_src_only','generated_bundle_only','compile_policy_once_per_search',
    'host_alias_resolution_retained','host_partitioning_retained','host_candidate_cache_retained',
    'host_top_k_retained','host_hydration_retained','host_quota_exposure_retained',
    'host_snapshot_retained','controller_contract_unchanged'
  ].forEach(key => { if (candidate[key] !== true) fail('candidate invariant must remain true: ' + key); });
  if (candidate.browser_surface_expanded !== false || candidate.customer_visible_behavior_authorized !== false) {
    fail('candidate browser/customer authority drift');
  }
  const authority = lock.release_authority || {};
  [
    'current_src_mutation','clasp_push','apps_script_head_mutation','script_properties_mutation',
    'version_creation','deployment_repoint','runtime_inventory_search_cutover','production_promotion'
  ].forEach(key => { if (authority[key] !== false) fail('release authority must remain false: ' + key); });
}

function inventoryArtifactContract() {
  return {
    label: 'inventory search',
    getSpec(lock) { return lock.inventory_bundle || {}; },
    installFilename: '31_EREIInventorySearchPolicy.gs',
    manifestFields(spec) {
      return {
        artifact_type: spec.artifact_type,
        artifact_id: spec.bundle_artifact_id,
        source_entrypoint: spec.source_entrypoint,
        exposed_global: spec.exposed_global,
        runtime_target: spec.runtime_target,
        module_count: spec.module_count,
        node_module_system_required_at_runtime: spec.node_module_system_required_at_runtime,
        package_root_only: spec.package_root_only,
        deep_imports_exposed: spec.deep_imports_exposed,
        bundle_sha256: spec.sha256
      };
    },
    manifestArrays(spec) {
      return {
        source_modules: spec.source_modules || [],
        external_commonjs_requires_not_bundled: spec.external_commonjs_requires_not_bundled || []
      };
    },
    requiredMethods: ['normalizeFilters','compileFilters','evaluateCandidate','budgetDistance','compareCandidates','rankEligible']
  };
}

function verifyArtifact(lock, artifactDir) {
  return PortableHostCandidateBuilder.verifyArtifact(lock, path.resolve(artifactDir), inventoryArtifactContract());
}

function replaceExact(source, from, to, label) {
  const first = source.indexOf(from);
  if (first < 0) fail(label + ' marker not found');
  if (source.indexOf(from, first + from.length) >= 0) fail(label + ' marker is not unique');
  return source.slice(0, first) + to + source.slice(first + from.length);
}

function patchSearchService(source, globalName) {
  const oldNormalize = `  function normalizeFilters_(f){\n    f=f||{}; return {city:normalizeString_(f.city),area:normalizeString_(f.area),developer_id:normalizeString_(f.developer_id),project_id:normalizeString_(f.project_id),developer_name:normalizeString_(f.developer),project_name:normalizeString_(f.project),unit_type:normalizeString_(f.unit_type),finishing_type:normalizeString_(f.finishing_type),status:normalizeString_(f.status),price_min:toNumberOrNull_(f.price_min),price_max:toNumberOrNull_(f.price_max),area_min:toNumberOrNull_(f.area_min),area_max:toNumberOrNull_(f.area_max),dp_max_pct:toNumberOrNull_(f.dp_max_pct),installment_years_min:toNumberOrNull_(f.installment_years_min),delivery_year_max:toNumberOrNull_(f.delivery_year_max),bedrooms_min:toNumberOrNull_(f.bedrooms_min)};\n  }`;
  const newNormalize = `  function normalizeFilters_(f){\n    return ${globalName}.normalizeFilters(f||{});\n  }`;

  const oldMatches = `  function matches_(o,f){\n    if(f.city&&normalizeLower_(o.city)!==normalizeLower_(f.city))return false;\n    if(f.area&&normalizeLower_(o.area)!==normalizeLower_(f.area))return false;\n    if(f.developer_id&&normalizeString_(o.developer_id)!==f.developer_id)return false;\n    if(f.project_id&&normalizeString_(o.project_id)!==f.project_id)return false;\n    if(f.unit_type&&normalizeLower_(o.unit_type)!==normalizeLower_(f.unit_type))return false;\n    if(f.finishing_type&&normalizeLower_(o.finishing_type)!==normalizeLower_(f.finishing_type))return false;\n    if(f.status&&normalizeLower_(o.status)!==normalizeLower_(f.status))return false;\n    var price=toNumberOrNull_(o.price),size=toNumberOrNull_(o.size),dp=toNumberOrNull_(o.dp_pct),term=toNumberOrNull_(o.installment_years),delivery=toNumberOrNull_(o.delivery_year),beds=toNumberOrNull_(o.project_max_bedrooms);\n    if(f.price_min!==null&&(price===null||price<f.price_min))return false;\n    if(f.price_max!==null&&(price===null||price>f.price_max))return false;\n    if(f.area_min!==null&&(size===null||size<f.area_min))return false;\n    if(f.area_max!==null&&(size===null||size>f.area_max))return false;\n    if(f.dp_max_pct!==null&&(dp===null||dp>f.dp_max_pct))return false;\n    if(f.installment_years_min!==null&&(term===null||term<f.installment_years_min))return false;\n    if(f.delivery_year_max!==null&&(delivery===null||delivery>f.delivery_year_max))return false;\n    if(f.bedrooms_min!==null&&(beds===null||beds<f.bedrooms_min))return false;\n    return true;\n  }\n  function budgetDistance_(o,f){var p=toNumberOrNull_(o.price);if(p===null)return 1e18;if(f.price_max!==null&&p>f.price_max)return p-f.price_max;if(f.price_min!==null&&p<f.price_min)return f.price_min-p;return 0;}`;
  const newMatches = `  function matches_(o,compiledPolicy){\n    return ${globalName}.evaluateCandidate(o,compiledPolicy).eligible===true;\n  }`;

  let out = replaceExact(source, oldNormalize, newNormalize, 'normalizeFilters');
  out = replaceExact(out, oldMatches, newMatches, 'eligibility policy');

  const resolveLine = `    var f=resolveHumanNames_(RuntimeHotPathV9.canonicalizeFilters(normalizeFilters_(req.filters||{})));`;
  out = replaceExact(out, resolveLine, resolveLine + `\n    var compiledInventorySearchPolicy_=${globalName}.compileFilters(f);`, 'compiled inventory search policy');

  const oldComparator = `      var cmp=function(a,b){var da=budgetDistance_(a,f),db=budgetDistance_(b,f);if(da!==db)return da-db;var pa=toNumberOrNull_(a.price)||1e18,pb=toNumberOrNull_(b.price)||1e18;if(pa!==pb)return pa-pb;return normalizeString_(a.unit_id).localeCompare(normalizeString_(b.unit_id));};`;
  const newComparator = `      var cmp=function(a,b){return ${globalName}.compareCandidates(a,b,compiledInventorySearchPolicy_);};`;
  out = replaceExact(out, oldComparator, newComparator, 'ranking comparator');
  out = replaceExact(out, `        if(matches_(o,f)){if(knownTotal===null)totalMatches++;insertTopK_(o);}`, `        if(matches_(o,compiledInventorySearchPolicy_)){if(knownTotal===null)totalMatches++;insertTopK_(o);}`, 'eligibility call');
  return out;
}

function mutateInventoryCandidate({ lock, outputDir }) {
  const searchPath = path.join(outputDir, '32_SearchService.gs');
  const originalSearch = fs.readFileSync(searchPath, 'utf8');
  fs.writeFileSync(searchPath, patchSearchService(originalSearch, lock.inventory_bundle.exposed_global), 'utf8');
}

function verifyInventoryCandidate({ lock, outputDir, srcDir }) {
  const searchPath = path.join(outputDir, '32_SearchService.gs');
  const candidateSearch = fs.readFileSync(searchPath, 'utf8');
  [
    lock.inventory_bundle.exposed_global + '.normalizeFilters',
    lock.inventory_bundle.exposed_global + '.compileFilters',
    lock.inventory_bundle.exposed_global + '.evaluateCandidate',
    lock.inventory_bundle.exposed_global + '.compareCandidates'
  ].forEach(token => { if (!candidateSearch.includes(token)) fail('candidate inventory delegation missing: ' + token); });
  [
    "if(f.city&&normalizeLower_(o.city)!==normalizeLower_(f.city))return false;",
    "if(f.price_min!==null&&(price===null||price<f.price_min))return false;",
    "var cmp=function(a,b){var da=budgetDistance_(a,f)"
  ].forEach(token => { if (candidateSearch.includes(token)) fail('candidate retains local inventory business rule: ' + token); });
  [
    'RuntimeHotPathV9.canonicalizeFilters', 'resolveHumanNames_', 'searchWindow_',
    'SearchCandidateCacheRepository.open()', 'hydratePageV7_',
    'RegistryRepository.precheckSearchUsage', 'RegistryRepository.reserveSearchUsage',
    'queueSnapshotV9_', 'writeSnapshot_', 'insertTopK_'
  ].forEach(token => { if (!candidateSearch.includes(token)) fail('required host responsibility missing: ' + token); });

  const currentController = fs.readFileSync(path.join(srcDir, '50_Controller.gs'), 'utf8');
  const candidateController = fs.readFileSync(path.join(outputDir, '50_Controller.gs'), 'utf8');
  if (candidateController !== currentController) fail('candidate Controller changed');
  if (candidateController.includes(lock.inventory_bundle.exposed_global)) fail('generated inventory policy leaked into Controller/browser dispatch');
}

function createInventoryEvidence({ lock, lockPath }) {
  return {
    schema_version: '1.0',
    candidate_id: 'EREI-INVENTORY-SEARCH-HOST-CANDIDATE-V1',
    source_lock: path.relative(ROOT, lockPath).split(path.sep).join('/'),
    authoritative_database_commit: lock.source.commit,
    upstream_workflow_run_id: lock.source.workflow_run_id,
    upstream_artifact_id: lock.source.artifact_id,
    upstream_archive_digest: lock.source.archive_digest,
    inventory_bundle_artifact_id: lock.inventory_bundle.bundle_artifact_id,
    inventory_bundle_sha256: lock.inventory_bundle.sha256,
    inventory_manifest_sha256: lock.inventory_bundle.manifest_sha256,
    exposed_global: lock.inventory_bundle.exposed_global,
    deterministic_inventory_policy_primary_in_candidate: true,
    policy_compiled_once_per_search: true,
    host_alias_resolution_retained: true,
    host_partitioning_retained: true,
    host_candidate_cache_retained: true,
    host_top_k_retained: true,
    host_hydration_retained: true,
    host_quota_exposure_retained: true,
    host_snapshot_retained: true,
    controller_contract_unchanged: true,
    browser_surface_expanded: false,
    clasp_push_performed: false,
    apps_script_head_mutated: false,
    script_properties_mutated: false,
    deployment_mutated: false,
    runtime_cutover_authorized: false
  };
}

function buildCandidate(options = {}) {
  return PortableHostCandidateBuilder.run({
    rootDir: ROOT,
    lockPath: options.lockPath || DEFAULT_LOCK,
    artifactDir: options.artifactDir,
    srcDir: options.srcDir || DEFAULT_SRC,
    outputDir: options.outputDir || DEFAULT_OUT,
    evidencePath: options.evidencePath || DEFAULT_EVIDENCE,
    validateLock,
    artifact: inventoryArtifactContract(),
    mutateCandidate: mutateInventoryCandidate,
    verifyCandidate: verifyInventoryCandidate,
    createEvidence: createInventoryEvidence
  });
}

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (key === '--artifact-dir') args.artifactDir = argv[++i];
    else if (key === '--lock') args.lockPath = argv[++i];
    else if (key === '--src') args.srcDir = argv[++i];
    else if (key === '--out') args.outputDir = argv[++i];
    else if (key === '--evidence') args.evidencePath = argv[++i];
    else fail('unknown argument: ' + key);
  }
  return args;
}

if (require.main === module) {
  try {
    const result = buildCandidate(parseArgs(process.argv.slice(2)));
    process.stdout.write('PASS inventory-search host candidate ' + result.evidence.candidate_digest + '\n');
  } catch (error) {
    console.error('FAIL inventory-search host candidate: ' + error.message);
    process.exitCode = 1;
  }
}

module.exports = Object.freeze({
  buildCandidate,
  patchSearchService,
  verifyArtifact,
  validateLock,
  digestTree: PortableHostCandidateBuilder.digestTree
});
