# Releasing

There are two ways to ship a new version. They share one rule: the integration
`manifest.json` version, the frontend `package.json` version and the
`ballinoraMatchCardVersion` constant must all match the release tag.

## One command (on any machine with Node 20+)

```bash
node script/release.mjs bump patch       # or: minor | major | next 1.2.3
```

What it does:

1. Reads the current version from `manifest.json`.
2. Bumps `manifest.json`, `frontend/package.json` and the card version constant
   in `frontend/src/ballinora-match-card.js`.
3. Rebuilds `frontend/dist/ballinora-match-card.js` so the bundle carries the
   new version too.
4. Commits the result as `Release vX.Y.Z` and tags it `vX.Y.Z`.

If the build fails, every file is reverted automatically.

Flags:

| Flag | Effect |
| --- | --- |
| `--no-commit` | Bump + rebuild only; print the commit/tag commands for you to run. |
| `--push` | Push the branch and the `vX.Y.Z` tag to `origin`. |

## Fully automatic (GitHub Actions)

Just push a `v*` tag and the [release workflow](../.github/workflows/release.yml)
does the rest:

1. Runs a clean `npm ci` + `npm run build` of the card.
2. Fails unless the tag matches `manifest.json` and the card version constant.
3. Drafts a GitHub Release named `vX.Y.Z` with a changelog of the commits since
   the previous version tag, and publishes it.

So the manual path is optional: you can commit the version bump yourself and
push a tag, and never run the script locally.

```bash
git tag v1.1.0 && git push origin v1.1.0
```

HACS then picks the release up from the tag (no artifacts need attaching — the
card bundle ships in the repository and `hacs.json` points at it).

## Prerelease check

- Frontend: `npm ci --prefix frontend && npm run test --prefix frontend`
- Integration: `node script/release.mjs bump patch --no-commit` first, then run
  `pytest` per `docs/testing.md` so tests exercise the new version.

## First release

If no `v*` tag exists yet, the workflow treats the entire commit history as the
changelog for the first release.