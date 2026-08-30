#!/usr/bin/env node
/**
 * Release helper for the Ballinora Match Tracker.
 *
 * Bumps the integration manifest version, the frontend package version and the
 * card version constant in one go, rebuilds the card bundle, then optionally
 * commits and tags the release.
 *
 *   node script/release.mjs next <1.2.3>      explicit next version
 *   node script/release.mjs bump <patch|minor|major>   bump current version
 *   --no-commit   do not commit or tag
 *   --push        also push the branch and tag to origin
 *
 * The script never touches network credentials; pushing is left to you (or the
 * CI release workflow, which triggers on the v* tag).
 */

import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const MANIFEST = path.join(ROOT, "custom_components", "ballinora_match_tracker", "manifest.json");
const PKG_JSON = path.join(ROOT, "frontend", "package.json");
const CARD_SRC = path.join(ROOT, "frontend", "src", "ballinora-match-card.js");

const SEMVER = /^\d+\.\d+\.\d+$/;

function json(file) {
  return JSON.parse(readFileSync(file, "utf8"));
}

function writeJson(file, value) {
  writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
}

function currentVersion() {
  return json(MANIFEST).version;
}

function bump(current, segment) {
  const [major, minor, patch] = current.split(".").map(Number);
  if (segment === "major") return `${major + 1}.0.0`;
  if (segment === "minor") return `${major}.${minor + 1}.0`;
  if (segment === "patch") return `${major}.${minor}.${patch + 1}`;
  throw new Error(`Unknown bump segment: ${segment}`);
}

function parseArgs() {
  const args = process.argv.slice(2);
  const mode = args.find((a) => a === "next" || a === "bump");
  const value = args.find((a) => !a.startsWith("--") && a !== "next" && a !== "bump");
  const push = args.includes("--push");
  const noCommit = args.includes("--no-commit");
  if (!mode || !value) {
    throw new Error(
      "Usage: node script/release.mjs next <x.y.z> | node script/release.mjs bump <patch|minor|major> [--no-commit] [--push]"
    );
  }
  if (mode === "next" && !SEMVER.test(value)) {
    throw new Error(`Invalid semver: ${value}`);
  }
  return { mode, value, push, noCommit };
}

function rewriteCardVersion(next) {
  const original = readFileSync(CARD_SRC, "utf8");
  // Anchor on the exact export so we never touch another string.
  const re = /(export const ballinoraMatchCardVersion = ")(\d+\.\d+\.\d+)(")/;
  const match = original.match(re);
  if (!match) throw new Error("Could not find ballinoraMatchCardVersion in card source");
  writeFileSync(CARD_SRC, original.replace(re, `$1${next}$3`));
}

function buildCard() {
  execFileSync("npm", ["--prefix", path.join(ROOT, "frontend"), "run", "build"], {
    stdio: "inherit",
    cwd: ROOT,
  });
}

function git(args) {
  return execFileSync("git", args, { cwd: ROOT, stdio: ["ignore", "pipe", "inherit"] })
    .toString()
    .trim();
}

function refExists(name) {
  try {
    execFileSync("git", ["rev-parse", "-q", "--verify", name], {
      cwd: ROOT,
      stdio: "ignore",
    });
    return true;
  } catch {
    return false;
  }
}

function main() {
  const { mode, value, push, noCommit } = parseArgs();
  const current = currentVersion();
  const next = mode === "next" ? value : bump(current, value);

  if (next === current) {
    throw new Error(`Next version equals current (${current}); nothing to do.`);
  }

  if (!noCommit && refExists(`refs/tags/v${next}`)) {
    throw new Error(`Tag v${next} already exists; refusing to roll forward. Use a higher version.`);
  }

  console.log(`Releasing ${current} → ${next}`);

  const snapshots = new Map();
  const track = { MANIFEST: MANIFEST, PKG_JSON: PKG_JSON, CARD_SRC: CARD_SRC };
  for (const [name, file] of Object.entries(track)) {
    snapshots.set(file, readFileSync(file));
  }

  try {
    const manifest = json(MANIFEST);
    manifest.version = next;
    writeJson(MANIFEST, manifest);

    const pkg = json(PKG_JSON);
    pkg.version = next;
    writeJson(PKG_JSON, pkg);

    rewriteCardVersion(next);
    buildCard();
  } catch (err) {
    for (const [file, bytes] of snapshots) writeFileSync(file, bytes);
    console.error(`Build/version failed — reverted: ${err.message}`);
    process.exit(1);
  }

  const dry = noCommit ? " (not committed)" : "";
  console.log("Versions bumped, card rebuilt.");

  if (noCommit) {
    console.log("Next: commit the changes and tag with v" + next);
    return;
  }

  git(["add", "custom_components/ballinora_match_tracker/manifest.json", "frontend/package.json", CARD_SRC, "frontend/dist/ballinora-match-card.js"]);
  git(["commit", "-m", `Release v${next}`]);
  git(["tag", `v${next}`]);
  console.log(`Committed and tagged v${next}.`);

  if (push) {
    git(["push", "origin", "HEAD"]);
    git(["push", "origin", `v${next}`]);
    console.log("Pushed branch and tag.");
  } else {
    console.log("Push with: git push origin HEAD && git push origin v" + next);
  }
}

try {
  main();
} catch (err) {
  console.error(`Release aborted: ${err.message}`);
  process.exit(1);
}