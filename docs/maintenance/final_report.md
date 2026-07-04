# Final hardening report — nirs4all-org

**Date:** 2026-07-04 · **Branch:** `main` · **Operator:** Claude (Opus 4.8) · **Reviewer:** Codex CLI 0.142.5

## Summary
Pragmatic hardening of the static landing page: added a web-appropriate community-health set and
SHA-pinned the workflow actions. **No change to site content** (`index.html`, assets, sitemaps untouched).

## Baseline / commit
- **Baseline HEAD:** `401122b` (origin/main).
- **Commit:** *(this commit)* — community-health + SHA-pins + docs/maintenance.

## Files
Added: `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CONTRIBUTING.md`, `.editorconfig`, `.pre-commit-config.yaml`
(hygiene-only — no Python gate), `.github/dependabot.yml` (github-actions + npm),
`docs/maintenance/{repository_audit,quality_gates,final_report}.md` + `codex_reviews/03`.
Modified: `.github/workflows/version-guard.yml` (2 action SHA-pins).
Not added: `CITATION.cff` (a landing page is not citable software).

## Checks
- Non-code change; site content untouched. YAML validated. `version-guard` is the only CI gate.
- **Codex Gate 3** — see `codex_reviews/03`.

## GitHub Actions (this push)
`version-guard [push]` — verified green post-push. Pushing `main` also updates the live `nirs4all.org`
Pages site; this diff does not touch any served asset.

## Residual risks / roadmap
- No link-checker / HTML validation CI yet (roadmap).
- Ensure `package.json` version and any `v*` tag stay reconciled (version-guard enforces one direction).

## 12-month maintenance
- Merge Dependabot PRs (actions + npm) after CI-green.
- Keep sitemaps/robots in sync with the pages; review any content change before merging to `main` (it's live).
