# nirs4all.org

Official landing page for the public nirs4all ecosystem: the Python
reference/oracle package, [nirs4all Studio](https://github.com/GBeurier/nirs4all-studio),
the client-side WASM web app, the shared UI package, the provider client layer,
and the v1 RC package topology.

Repository name: `nirs4all-org`

Visible at [nirs4all.org](https://nirs4all.org)

The public [open-source NIRS tools hub](https://nirs4all.org/open-source-nirs-tools.html)
maps the nirs4all file readers, datasets, methods engine, browser modelling app,
pipeline repository, papers archive, benchmarks, and release cockpit.

## Local preview

Open `index.html` directly in any browser — no server needed.

## Structure

```
nirs4all-org/
├── index.html              # The entire landing page (HTML + CSS + JS)
├── assets/                 # Logos and screenshots
│   ├── brand/              # Ecosystem and per-package brand kits
│   │   ├── nirs4all-ui/
│   │   ├── nirs4all-core/
│   │   └── nirs4all-providers/
│   ├── institutions/
│   ├── partners/
│   └── screenshots_studio/
├── CNAME                   # GitHub Pages custom domain
├── robots.txt
├── sitemap.xml
└── sitemap-index.xml
```

## Content

- **Hero**: Logo, tagline, install command, CTA buttons
- **Overview**: Python reference library vs Studio comparison
- **RC topology**: `nirs4all-core` as the V1 RC portable aggregate,
  `nirs4all-lite` as a compatibility alias during cutover, `web.nirs4all.org` as
  client-side-only/WASM, `nirs4all-ui` as the shared Studio/Web reusable
  components/assets package, and `nirs4all-providers` as the soft-importing
  read-side client layer over datasets and repository
- **Features**: 6 key capability cards
- **Screenshots**: Tabbed gallery of Studio UI
- **Quick Start**: Tabbed code blocks (install, basic usage, advanced pipelines)
- **Team**: Gregory Beurier, Denis Cornet, Lauriane Rouan
- **Institutions**: CIRAD + UMR AGAP Institut
- **Publications**: Research papers using nirs4all + BibTeX citation
- **Resources**: All links (GitHub, Docs, PyPI, institutions)

## Credits

Developed at [CIRAD](https://www.cirad.fr) / [UMR AGAP Institut](https://umr-agap.cirad.fr)
by Gregory Beurier, Denis Cornet, and Lauriane Rouan.

## License

The site is dual-licensed open-source — **`CeCILL-2.1 OR AGPL-3.0-or-later`** — with an
optional **commercial license**. For any commercial use, contact
<nirs4all-admin@cirad.fr>. See [`LICENSING.md`](LICENSING.md) and [`LICENSES/`](LICENSES/).
Logos, fonts and partner/institution assets remain under their own terms.
