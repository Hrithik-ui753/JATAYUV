/**
 * Integrity tests for the 3D viewer and upload UI (no browser required).
 *
 * Run with: npm test
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import test from "node:test";

import { PLYLoader } from "three/examples/jsm/loaders/PLYLoader.js";

import {
  EMPTY_RECONSTRUCTION_MESSAGE,
  isUsablePointCloud,
  resolveViewerState,
  uploadOutcome,
  validateArtifactUrl,
} from "../src/lib/integrity.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const viewerDir = path.join(here, "..", "src", "components", "viewer");

function validPly(vertices = 3) {
  const rows = Array.from({ length: vertices }, (_, i) => `${i}.0 ${i * 0.5} ${i * 2.0} 255 128 0`);
  return [
    "ply",
    "format ascii 1.0",
    `element vertex ${vertices}`,
    "property float x",
    "property float y",
    "property float z",
    "property uchar red",
    "property uchar green",
    "property uchar blue",
    "end_header",
    ...rows,
    "",
  ].join("\n");
}

test("viewer without an artifact shows the required empty state", () => {
  assert.equal(
    EMPTY_RECONSTRUCTION_MESSAGE,
    "No verified 3D reconstruction available yet. Process a drone mission to generate one."
  );
  const state = resolveViewerState({});
  assert.equal(state.status, "empty");
  assert.equal(state.message, EMPTY_RECONSTRUCTION_MESSAGE);
});

test("artifact URLs are validated before loading", () => {
  assert.equal(validateArtifactUrl("/storage/reconstructions/a.ply", [".ply"]).valid, true);
  assert.equal(validateArtifactUrl("http://localhost:8000/storage/a.ply", [".ply"]).valid, true);
  assert.equal(validateArtifactUrl("javascript:alert(1)", [".ply"]).valid, false);
  assert.equal(validateArtifactUrl("//evil.example/a.ply", [".ply"]).valid, false);
  assert.equal(validateArtifactUrl("relative/no-slash.ply", [".ply"]).valid, false);
  assert.equal(validateArtifactUrl("/storage/a.glb", [".ply"]).valid, false);
  assert.equal(validateArtifactUrl("", [".ply"]).valid, false);

  const invalid = resolveViewerState({ plyUrl: "javascript:alert(1)" });
  assert.equal(invalid.status, "error");
  assert.match(invalid.message, /scheme/i);
});

test("PLY loader parses a valid point cloud", () => {
  const bytes = new TextEncoder().encode(validPly(4));
  const geometry = new PLYLoader().parse(bytes.buffer);
  const position = geometry.getAttribute("position");
  assert.equal(position.count, 4);
  assert.equal(geometry.getAttribute("color").count, 4);
  assert.equal(isUsablePointCloud(geometry), true);
  geometry.dispose();
});

test("PLY loader rejects invalid files instead of inventing vertices", () => {
  const encoder = new TextEncoder();

  // Garbage bytes yield zero vertices.
  const garbage = new PLYLoader().parse(encoder.encode("this is not a ply file").buffer);
  assert.equal(isUsablePointCloud(garbage), false);
  garbage.dispose();

  // A header that claims vertices but has no body yields NaN coordinates, which
  // must be rejected rather than rendered as a cloud.
  const truncated = ["ply", "format ascii 1.0", "element vertex 5", "property float x",
    "property float y", "property float z", "end_header", ""].join("\n");
  const broken = new PLYLoader().parse(encoder.encode(truncated).buffer);
  assert.equal(isUsablePointCloud(broken), false);
  broken.dispose();
});

test("upload outcome never reports a failed upload as success", () => {
  assert.equal(uploadOutcome({ ok: true, uploadedCount: 3 }).kind, "success");
  assert.match(uploadOutcome({ ok: true, uploadedCount: 3 }).message, /3 aerial frame/);

  const empty = uploadOutcome({ ok: true, uploadedCount: 0 });
  assert.equal(empty.kind, "error");

  const failed = uploadOutcome({ ok: false, errorMessage: "HTTP 413 file too large" });
  assert.equal(failed.kind, "error");
  assert.match(failed.message, /HTTP 413 file too large/);
  assert.doesNotMatch(failed.message, /completed|simulation/i);
});

test("production viewers contain no procedural geometry generation", () => {
  for (const file of ["AdvancedSpatialViewer3D.tsx", "PointCloudViewer.tsx"]) {
    const source = readFileSync(path.join(viewerDir, file), "utf8");
    assert.doesNotMatch(source, /Math\.random/, `${file} must not generate random geometry`);
    assert.match(source, /PLYLoader/, `${file} must load real PLY artifacts`);
    assert.match(source, /EMPTY_RECONSTRUCTION_MESSAGE/, `${file} must use the shared empty state`);
    assert.doesNotMatch(source, /Upload completed with local simulation/, `${file} sanity`);
  }

  const viewer = readFileSync(path.join(viewerDir, "AdvancedSpatialViewer3D.tsx"), "utf8");
  assert.match(viewer, /GLTFLoader/, "the 3D viewer must support real GLB/GLTF meshes");
});

test("dashboard upload handler contains no false-success message", () => {
  const dashboard = readFileSync(
    path.join(here, "..", "src", "app", "dashboard", "page.tsx"),
    "utf8"
  );
  assert.doesNotMatch(dashboard, /Upload completed with local simulation/);
  assert.match(dashboard, /uploadOutcome\(/);
});
