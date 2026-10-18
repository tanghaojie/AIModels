/** Asset-only reproduction with the consumer's installed Cesium source, no browser/WebGL.
 * node verify_tileset_selection.mjs <absolute path to @cesium/engine>
 */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const engine = process.argv[2];
assert(engine && path.isAbsolute(engine), 'Pass the installed @cesium/engine directory');
const project = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const tilesetPath = path.resolve(project, '../../model-assets/geo-context/wangjing-soho-1500-v1/tileset.json');
const tileset = JSON.parse(readFileSync(tilesetPath, 'utf8'));
const version = JSON.parse(readFileSync(path.join(engine, 'package.json'), 'utf8')).version;
const tileSource = path.join(engine, 'Source/Scene/Cesium3DTile.js');
const traversalSource = path.join(engine, 'Source/Scene/Cesium3DTilesetBaseTraversal.js');
// Use the package entry point to preserve Cesium's circular module initialization order.
const { Cesium3DTile: Tile } = await import(pathToFileURL(path.join(engine, 'index.js')));
const frame = {
  mode: 3, pixelRatio: 1,
  context: { drawingBufferWidth: 1560, drawingBufferHeight: 849 },
  camera: { frustum: { sseDenominator: 2 * Math.tan(Math.PI / 6) } },
};
const maximumScreenSpaceError = 16;
function selection(error, distance) {
  const tile = {
    _tileset: { _scaledGeometricError: error, dynamicScreenSpaceError: false },
    geometricError: tileset.root.geometricError, _distanceToCamera: distance,
  };
  const sse = Tile.prototype.getScreenSpaceError.call(tile, frame, true);
  return { error, distance_m: distance, screen_space_error: sse,
    rejected_by_base_traversal_sse_gate: sse <= maximumScreenSpaceError };
}
const before = selection(0, 2000);
const after = [500, 2000, 5000, 10000, 30000].map(d => selection(tileset.geometricError, d));
assert(before.rejected_by_base_traversal_sse_gate);
assert.equal(tileset.root.geometricError, 0);
assert(after.every(x => !x.rejected_by_base_traversal_sse_gate));
const sha256 = p => createHash('sha256').update(readFileSync(p)).digest('hex');
const report = {
  scope: 'Asset-level Cesium SSE calculation; no browser, WebGL, or visual acceptance',
  engine_version: version, maximum_screen_space_error: maximumScreenSpaceError,
  source: { tile: sha256(tileSource), base_traversal: sha256(traversalSource) },
  tileset_sha256: sha256(tilesetPath), before, after, passed: true,
};
writeFileSync(path.join(project, 'verification/tileset-selection.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
