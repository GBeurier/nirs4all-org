# Org contributor instructions

## Static presentation and LIVE boundary

Org is public presentation, not runtime authority: hand-authored index.html/open-source-nirs-tools.html, inline CSS/vanilla JS, no framework/build; package.json is version metadata only. Siblings are links, not architectural dependencies; versions/ABI/line counts are historical, not support.
Pushing main updates LIVE (Pages main from /); preserve CNAME=nirs4all.org, green main and content review. Examples/tags/links grant no push/deploy/frontend authority. Preview index.html directly; optional version/analytics requests degrade gracefully offline.

## Unique content and asset constraints

Navigate by section comment markers, not old offsets. CSS stays in labelled inline blocks/:root, no new stylesheet. Reuse section-paper/section-dark/section-aurora/section-alt backdrops.
Version badges/buttons reuse data-lib-version/data-studio-version and prefix data-* hooks for existing PyPI/GitHub lookups/download updates, never hardcoded versions.
Use full assets subdirectory paths: logos_ecosystem/, institutions/, screenshots_studio/, authors/, partners/. Keep *.pptx and *:Zone.Identifier source streams excluded from deployment.
For authorized page/screenshot/content changes synchronize sitemap.xml, sitemap-index.xml, robots.txt, lastmod/image locations and head title/description/canonical/hreflang/JSON-LD/OG/Twitter with actual content. Keep the static no-server/no-database/no-user-data boundary and [private security reporting](SECURITY.md); library issues go to their owner.

## Checks, receipts and rights

From this checkout use [README projection/validation/unittest gates](README.md#release-manifest-staging), including explicitly selected `../nirs4all-ecosystem/docs/contracts/release/aggregation-lock.n4a.lock.json`. The projector emits NO downloads; source selection is not public-artifact proof.
Retain README unittest despite quality-page no-tests history. [Hooks/preview](docs/maintenance/quality_gates.md#local-checks) keep fetch/prerequisite conditions. Version-guard: package.json not ahead of latest v* tag; notable releases retain that duty under separate authority.
Keep native-candidate-staging.json byte-identical with Cockpit; no V1 announcement/download links before lock-authorized publication. Preserve immutable receipt/profile/governance identity; historical README hashes do not replace checking selected current inputs.
[LICENSING](LICENSING.md#4-repository-scope) and [notices](THIRD_PARTY_NOTICES.md) retain project source/content `CeCILL-2.1 OR AGPL-3.0-or-later`, optional commercial terms/contact, SPDX/contribution terms and separate dataset/logo/font/institution/third-party licence/DOI rights.

## Working rules

Read applicable instructions first and preserve dirty work. If `../AGENTS.md` exists, read it within the current user scope; this file also works alone.
Use CodeGraph FIRST only with this checkout's own `.codegraph/` (exact projectPath or local CLI); never auto-index or use an ancestor index. Source, tests and builds are final authority.
Record actual commands, exits and skips. Keep secrets, private data and build output out of Git. Examples grant no install, network, science, publication, hosting, frontend or Git authority.
All project content, including UI text, docs, tests, reports, PRs and commits, is English; conversation may be French. Preserve names, identifiers, quotations and provenance.
