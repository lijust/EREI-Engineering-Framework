'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const HOST_PLATFORM_DEPENDENCY = /SpreadsheetApp|DriveApp|UrlFetchApp|PropertiesService|LockService|google\.script\.run/;
const MODEL_AGENT_DEPENDENCY = /\bOpenAI\b|\bAnthropic\b|\bGemini\b|\bLangChain\b|\bCrewAI\b|\bAutoGen\b/i;

function fail(message) {
  throw new Error(message);
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function sha256(file) {
  return 'SHA256-' + crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex').toUpperCase();
}

function mkdirp(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function copyTree(source, destination) {
  fs.rmSync(destination, { recursive: true, force: true });
  mkdirp(destination);
  fs.cpSync(source, destination, { recursive: true });
}

function listFiles(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const full = path.join(dir, entry.name);
    return entry.isDirectory() ? listFiles(full) : [full];
  }).sort();
}

function digestTree(dir) {
  const hash = crypto.createHash('sha256');
  listFiles(dir).forEach(file => {
    const rel = path.relative(dir, file).split(path.sep).join('/');
    hash.update(rel + '\0');
    hash.update(fs.readFileSync(file));
    hash.update('\0');
  });
  return 'SHA256-' + hash.digest('hex').toUpperCase();
}

function exact(actual, expected, label) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) fail(label + ' drift');
}

function resolveFrom(rootDir, value) {
  return path.isAbsolute(value) ? value : path.resolve(rootDir, value);
}

function verifyArtifact(lock, artifactDir, artifact) {
  if (!artifact || typeof artifact.getSpec !== 'function') fail('artifact.getSpec is required');
  const spec = artifact.getSpec(lock) || {};
  const label = artifact.label || 'portable host candidate';
  const bundlePath = path.join(artifactDir, spec.filename || '');
  const manifestPath = path.join(artifactDir, spec.manifest_filename || '');

  if (!fs.existsSync(bundlePath)) fail(label + ' bundle missing');
  if (!fs.existsSync(manifestPath)) fail(label + ' manifest missing');
  if (sha256(bundlePath) !== spec.sha256) fail(label + ' bundle sha256 mismatch');
  if (sha256(manifestPath) !== spec.manifest_sha256) fail(label + ' manifest sha256 mismatch');

  const manifest = readJson(manifestPath);
  const fields = typeof artifact.manifestFields === 'function' ? artifact.manifestFields(spec) : {};
  Object.entries(fields || {}).forEach(([key, expected]) => {
    if (manifest[key] !== expected) fail(label + ' manifest ' + key + ' drift');
  });
  const arrays = typeof artifact.manifestArrays === 'function' ? artifact.manifestArrays(spec) : {};
  Object.entries(arrays || {}).forEach(([key, expected]) => {
    exact(manifest[key] || [], expected || [], label + ' ' + key);
  });

  const source = fs.readFileSync(bundlePath, 'utf8');
  if (spec.exposed_global && !new RegExp('\\bvar\\s+' + spec.exposed_global + '\\s*=').test(source)) {
    fail(label + ' global missing');
  }
  (artifact.requiredMethods || []).forEach(method => {
    if (!new RegExp('\\b' + method + '\\s*:').test(source)) fail(label + ' method missing: ' + method);
  });
  if (HOST_PLATFORM_DEPENDENCY.test(source)) fail('generated ' + label + ' bundle contains host/platform dependency');
  if (MODEL_AGENT_DEPENDENCY.test(source)) fail('generated ' + label + ' bundle contains model/agent dependency');
  if (typeof artifact.verify === 'function') artifact.verify({ lock, spec, manifest, source, bundlePath, manifestPath });

  return { spec, manifest, source, bundlePath, manifestPath };
}

function run(config = {}) {
  if (typeof config.validateLock !== 'function') fail('validateLock is required');
  if (typeof config.mutateCandidate !== 'function') fail('mutateCandidate is required');
  if (typeof config.verifyCandidate !== 'function') fail('verifyCandidate is required');
  if (typeof config.createEvidence !== 'function') fail('createEvidence is required');
  if (!config.artifactDir) fail('artifactDir is required');

  const rootDir = path.resolve(config.rootDir || process.cwd());
  const lockPath = resolveFrom(rootDir, config.lockPath);
  const artifactDir = resolveFrom(rootDir, config.artifactDir);
  const srcDir = resolveFrom(rootDir, config.srcDir);
  const outputDir = resolveFrom(rootDir, config.outputDir);
  const evidencePath = resolveFrom(rootDir, config.evidencePath);

  const lock = readJson(lockPath);
  config.validateLock(lock);
  const currentSrcDigestBefore = digestTree(srcDir);
  const verified = verifyArtifact(lock, artifactDir, config.artifact);

  copyTree(srcDir, outputDir);
  const installFilename = config.artifact && config.artifact.installFilename;
  if (!installFilename) fail('artifact.installFilename is required');
  fs.copyFileSync(verified.bundlePath, path.join(outputDir, installFilename));

  config.mutateCandidate({ lock, verified, outputDir });
  config.verifyCandidate({ lock, verified, outputDir, srcDir });

  const currentSrcDigestAfter = digestTree(srcDir);
  if (currentSrcDigestAfter !== currentSrcDigestBefore) fail('current src mutated while building portable host candidate');

  const customEvidence = config.createEvidence({
    lock,
    verified,
    outputDir,
    srcDir,
    lockPath,
    evidencePath,
    currentSrcDigestBefore,
    currentSrcDigestAfter
  }) || {};
  const evidence = Object.assign({}, customEvidence, {
    current_src_digest_before: currentSrcDigestBefore,
    current_src_digest_after: currentSrcDigestAfter,
    current_src_mutated: false,
    candidate_digest: digestTree(outputDir),
    generated_bundle_installed: true
  });

  mkdirp(path.dirname(evidencePath));
  fs.writeFileSync(evidencePath, JSON.stringify(evidence, null, 2) + '\n', 'utf8');
  return { lock, verified, evidence, outputDir, evidencePath };
}

module.exports = Object.freeze({
  run,
  verifyArtifact,
  digestTree,
  readJson,
  sha256
});
