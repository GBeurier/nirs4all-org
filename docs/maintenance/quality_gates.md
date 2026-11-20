# Quality gates — nirs4all-org

A static landing page (HTML/CSS/JS assets) with stdlib release-lock projection and validation tools. It has no framework or build step.

## Local checks

```bash
python scripts/validate_site.py
python -m unittest discover -s tests -v
uvx pre-commit run --all-files          # hygiene: trailing whitespace, EOF, YAML/JSON, private keys
# preview the site:
npx serve .                             # or open index.html in a browser
```

## CI gates (`.github/workflows/`)

| workflow | trigger | gate |
|---|---|---|
| `site-quality.yml` | push/PR | manifest boundaries, HTML, links, accessibility, SEO and release-manifest negative tests |
| `version-guard.yml` | push/PR | `package.json` version must not be ahead of the latest `v*` tag |

The site itself is published to `nirs4all.org` from `main` (GitHub Pages). The declared workflows are the authority for their action versions.

## Deepest-hardening roadmap

- Add a link-checker / HTML validator CI (e.g. `lychee` for broken links, `html-validate`).
- Add a Lighthouse/accessibility check on PRs.
- Keep `sitemap.xml` / `robots.txt` in sync with the pages that exist.
