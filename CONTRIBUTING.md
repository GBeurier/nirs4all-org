# Contributing to nirs4all-org

This repository is the static landing page for [nirs4all.org](https://nirs4all.org).

- Edit `index.html`, `open-source-nirs-tools.html`, and the assets under `assets/`.
- Keep the page self-contained and fast — avoid heavy external dependencies.
- Preview locally by opening the HTML in a browser (or `npx serve .`).
- Update `sitemap.xml` / `sitemap-index.xml` / `robots.txt` when you add or remove pages.
- Bump `package.json` `version` for a notable site release; the `version-guard` workflow keeps the
  manifest from getting ahead of the latest `v*` tag.
- **Pushing to `main` updates the live site** — keep `main` green and review content changes.

By contributing you agree to the `CeCILL-2.1 OR AGPL-3.0-or-later` license and the `CODE_OF_CONDUCT.md`.
