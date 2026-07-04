# Quality gates — nirs4all-org

A static landing page (HTML/CSS/JS assets). There is no application code or test suite.

## Local checks

```bash
uvx pre-commit run --all-files          # hygiene: trailing whitespace, EOF, YAML/JSON, private keys
# preview the site:
npx serve .                             # or open index.html in a browser
```

## CI gates (`.github/workflows/`)

| workflow | trigger | gate |
|---|---|---|
| `version-guard.yml` | push/PR | `package.json` version must not be ahead of the latest `v*` tag |

The site itself is published to `nirs4all.org` from `main` (GitHub Pages). All third-party actions are
**SHA-pinned** (Dependabot-tracked; github-actions + npm).

## Deepest-hardening roadmap

- Add a link-checker / HTML validator CI (e.g. `lychee` for broken links, `html-validate`).
- Add a Lighthouse/accessibility check on PRs.
- Keep `sitemap.xml` / `robots.txt` in sync with the pages that exist.
