# Repository audit — nirs4all-org

> Generated from the automated pre-release audit (workflow wf_1fc87351-29f); the **Deepest hardening roadmap** section records the fullest realistic hardening even where the pragmatic pass does not implement it. Reviewed at Codex Gate 1.

- **Mode:** IN SCOPE — pragmatic hardening + push
- **Baseline HEAD:** `05666f5`
- **Role:** Static landing page for nirs4all.org — a single hand-authored index.html (plus an open-source-tools hub page), served directly by GitHub Pages from the main branch.
- **Stack:** Static HTML/CSS/JS (no framework, no bundler). index.html (252 KB) has all HTML+CSS+JS inline. package.json is private:true with no dependencies and no scripts — it exists only to carry the version string. Node/npm nominally implied but no build. One GitHub Actions workflow uses Python 3.11 + 'packaging' (version-guard only). Deployed via GitHub Pages (built-in branch deploy, CNAME nirs4all.org, .nojekyll).

## Release-readiness verdict
nirs4all-org is a low-complexity static marketing site (single 252 KB inline index.html + an ecosystem hub page) served by GitHub Pages directly from main. CI is green and minimal: one hardened version-guard workflow (least-privilege permissions, blocks un-tagged version bumps) plus the implicit GitHub-managed Pages deploy. There are no build/test/lint/docs gates and none are truly needed, but the site can deploy broken HTML/links to production with zero validation. The main release-readiness gaps are push-safety (every push to main is an instant, ungated production deploy of nirs4all.org, with CNAME/.nojekyll unguarded), light CI supply-chain hygiene (actions pinned to mutable tags, no dependabot), and missing governance files (SECURITY/CITATION/CHANGELOG/etc.). Secret scan is clean. Recommended hardening: an explicit environment-gated Pages workflow plus PR-time HTML/link validation, then the low-risk quick wins.

## Gate commands (detected)
| key | value |
|---|---|
| `install` | — |
| `test` | — |
| `lint` | — |
| `typecheck` | — |
| `format` | — |
| `docs_build` | — |
| `package_build` | — |

## CI
- **Latest status:** All 8 most recent runs green (ok). Alternating 'version-guard' (repo workflow) and 'pages build and deployment' (GitHub-managed built-in Pages deploy, no workflow file). Latest: version-guard #28671233196 ok.
- **Workflows:**
- .github/workflows/version-guard.yml — version-guard: on push/PR to main and rc/**; single job 'guard' (ubuntu-latest); permissions: contents:read (least-privilege); asserts package.json version is not AHEAD of the latest v* git tag (blocks un-tagged version bumps merged to main)
- **Gaps:**
- No HTML/link validation, no a11y/Lighthouse, no SEO/sitemap validation — the site can deploy with broken links or invalid markup and CI stays green
- GitHub Pages deploy is the implicit branch-based 'pages build and deployment' (no workflow in repo) — deploy is ungated and unobservable in .github/workflows
- Actions pinned only to major tags (actions/checkout@v4, actions/setup-python@v5), not full commit SHA
- No dependabot/renovate to keep the two pinned actions patched

## Standard files
- **Present:** readme, license, gitignore
- **Missing:** changelog, contributing, security, code_of_conduct, citation, editorconfig, precommit, pr_template, issue_template, dependabot

## Packaging
- **name:** `nirs4all-org` — **version:** `1.0.0`
- **issues:**
- package.json is marked private:true with no scripts and no dependencies — it exists only to carry the version compared by version-guard.yml (VG_STRATEGY=npm_package_json), not to build/publish anything
- package.json version 1.0.0 matches tag v1.0.0, but the branch also carries non-v prefixed tags (n4a-v1-2026.07-refactor, n4a-v1-rc1-2026.07-refactor) that version-guard ignores (prefix 'v'); the rc/v1-full-refactor branch commits bump a 'core rc version to 0.2.2' referenced in content, a separate version namespace from this repo's 1.0.0 — mixed version vocabularies are a drift/confusion risk
- No packaged artifact: distribution is the raw HTML served by Pages; there is no build/bundle/minify step so index.html ships unminified (252 KB)

## Tests
- **framework:** None
- **estimate:** 0 tests
- **coverage:** No test or coverage config; not meaningful for a static single-page site (validation/link-checking would be the equivalent quality gate — see roadmap).

## Docs
- **system:** None. This repository IS the documentation/marketing surface: a single static index.html (252 KB, all HTML+CSS+JS inline) plus open-source-nirs-tools.html hub page. No mkdocs/Sphinx/RTD. README.md documents structure; 'Local preview' = open index.html in a browser (no build step).
- **status:** N/A — no docs generator to build; the HTML files are the deployable artifact served directly by GitHub Pages.

## Risks
| severity | area | detail |
|---|---|---|
| medium | deploy/push-safety | GitHub Pages deploys directly from the main branch via the built-in 'pages build and deployment' (visible in gh run list, no workflow file in .github/workflows). Any push to main goes live at nirs4all.org immediately with zero validation gate — a broken link, malformed HTML, or accidental CNAME/.nojekyll change ships to production. |
| low | ci-supply-chain | .github/workflows/version-guard.yml pins actions only to mutable major tags (actions/checkout@v4, actions/setup-python@v5) and installs 'packaging' from PyPI unpinned; no SHA pinning and no dependabot to track them. |
| low | governance | Missing SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, CHANGELOG.md, CITATION.cff, .editorconfig, issue/PR templates — below the governance bar of sibling ecosystem repos, despite a documented security contact (nirs4all-admin@cirad.fr in LICENSING.md). |
| low | quality-gate | No HTML validation, link checking, or a11y/SEO/Lighthouse checks. The two large hand-authored HTML files (index.html 252 KB, open-source-nirs-tools.html 16 KB) and the two sitemaps can rot with no automated detection. |
| low | version-hygiene | Two parallel version vocabularies coexist: this repo's package.json 1.0.0 / tag v1.0.0 vs the rc/v1-full-refactor branch's 'core rc 0.2.2' content and n4a-v1-* tags. version-guard only governs the v* line; content version claims are unguarded and can drift from reality. |

## Security
- **info** — Secret scan over tracked source (HTML/JS/JSON/YAML/XML) for private keys, aws_secret, api_key=, token=... found no plausible real leaks.
- **low** — index.html serves ~252 KB of inline JS/CSS with no Content-Security-Policy and no Subresource Integrity; acceptable for a static self-hosted page but leaves no defense-in-depth if any third-party asset/link is later inlined.
- **info** — version-guard.yml already applies least-privilege 'permissions: contents: read' — good baseline; no secrets are referenced by the workflow.

## Quick wins (pragmatic scope — safe to apply now)
- Add SECURITY.md (reuse the existing nirs4all-admin@cirad.fr contact from LICENSING.md) and a /.well-known/security.txt
- Pin actions/checkout@v4 and actions/setup-python@v5 to full commit SHAs in .github/workflows/version-guard.yml, and pip install packaging with a pinned version
- Add .github/dependabot.yml for the github-actions ecosystem (weekly)
- Add .editorconfig for the HTML/JSON/XML files
- Scaffold CHANGELOG.md and add CITATION.cff, CODE_OF_CONDUCT.md, CONTRIBUTING.md, plus .github/ISSUE_TEMPLATE and PULL_REQUEST_TEMPLATE for parity with sibling repos
- Add a lightweight PR-only link-check (lychee) and html5validator job — non-blocking to start — so markup/link rot surfaces before it deploys

## Deepest hardening roadmap (fullest realistic hardening)
- Replace the implicit branch-based Pages deploy with an explicit .github/workflows/pages.yml using actions/upload-pages-artifact + actions/deploy-pages, gated by a GitHub Environment (github-pages) with required reviewers/branch protection, concurrency group, and permissions: pages:write id-token:write only — makes production deploys observable and gateable
- Add a PR validation workflow: HTML validation (html5validator/vnu), dead-link checking (lycheeverse/lychee) across index.html + open-source-nirs-tools.html + sitemaps, and sitemap/robots consistency check
- Add Lighthouse CI (perf/a11y/SEO/best-practices) with a budget threshold as a required PR check on this user-facing marketing page
- Pin every GitHub Action to a full 40-char commit SHA and add .github/dependabot.yml (github-actions ecosystem, weekly) to track updates
- Add a Content-Security-Policy strategy for the inline JS/CSS in the 252 KB index.html (meta CSP or Pages headers) and consider extracting inline assets for SRI
- Publish /.well-known/security.txt and a SECURITY.md pointing to nirs4all-admin@cirad.fr (contact already exists in LICENSING.md)
- Add CITATION.cff, CHANGELOG.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, .editorconfig, and .github/ISSUE_TEMPLATE + PULL_REQUEST_TEMPLATE for governance parity with other ecosystem repos
- Add a scheduled external-link/uptime monitor (link rot on the ecosystem hub page open-source-nirs-tools.html) and a robots/sitemap freshness check tied to releases
- Document and CI-verify the CNAME custom-domain invariant (a lost/edited CNAME silently breaks nirs4all.org) — e.g. a guard step asserting CNAME==nirs4all.org and .nojekyll present

## Push-safety notes
- Production is branch-deployed: pushing to main triggers the GitHub-managed 'pages build and deployment' (seen in gh run list; NO workflow file gates it) and publishes to nirs4all.org instantly. There is no staging/review environment or validation gate between commit and live site.
- .github/workflows/version-guard.yml will FAIL CI on any push/PR to main or rc/** if package.json 'version' is bumped ahead of the latest v* tag — a version bump must ship as tag v<X.Y.Z> first, never merged to main un-tagged. Currently safe (1.0.0 == v1.0.0).
- CNAME (nirs4all.org) and .nojekyll at repo root are load-bearing for the Pages custom domain and asset serving; an accidental edit/removal in a push silently breaks the live domain and there is no guard asserting them.
- Editing sitemap-index.xml / sitemap.xml / robots.txt deploys straight to production SEO with no validation — mistakes ship live.
- The rc/v1-full-refactor branch is also covered by version-guard (rc/**), and its commits carry a separate 'core rc' version narrative; merging it to main could publish topology/version claims to the public landing page — treat rc→main merges as content-release events.
