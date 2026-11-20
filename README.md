# nirs4all.org

Official landing page for the public nirs4all ecosystem: the Python
reference/oracle package, [nirs4all Studio](https://github.com/GBeurier/nirs4all-studio),
the client-side WASM web app, the shared UI package, the provider client layer,
and the stable V1 package topology powered by DAG-ML.

Repository name: `nirs4all-org`

Visible at [nirs4all.org](https://nirs4all.org)

The public [open-source NIRS tools hub](https://nirs4all.org/open-source-nirs-tools.html)
maps the nirs4all file readers, datasets, methods engine, browser modelling app,
pipeline repository, papers archive, benchmarks, and release cockpit.

Current source selection is recorded in `release-manifest.json`, the explicit
`n4a.org-release-manifest/v2` projection of the selected ecosystem lock. Its train
identity and source status come from that lock. **Publication is not assessed by
this source lock; artifacts are not projected.** Selected packages may already
be published: existing registry badges/links report availability separately.
A final source status is not itself an artifact-publication receipt or a claim
of universal portability. Studio keeps its independently qualified pinned runtime;
its [latest stable release](https://github.com/GBeurier/nirs4all-studio/releases/latest)
and the current [common guide and API reference](https://gbeurier.github.io/nirs4all/)
remain separate from source selection. The
[Legacy guide](https://gbeurier.github.io/nirs4all/legacy/index.html) is historical.

The `release-status.html` page separates the current source cohort from the
**initial V1 publication history**. The original R2 projection is preserved
byte-for-byte as `release-manifest-r2-history.json`; both `r1-archive.html` and
`r2-archive.html` read this historical input, never the changing current endpoint.
Its SHA-256 is `3868dbe836cba25d5b681864fbbffb8178c011353800ad1310767ae461f48f32`.
The original annotated `v1.0.7` and `n4a-v1-2026.09-native-release` tags remain
historical. The immutable `native-candidate-staging.json` keeps governance commit
`d7d62825e5aa5ab5554ec7d084fab29be66acd74` and ledger SHA-256
`d7fec320b6906c192bd7388f3137436ab8875e135f440ce1461c89379b537450`.
Its distinct R1/R2/R3/R4 receipts qualify that historical V1 profile, not the
current owner cohort. Preserve its exact bytes and the byte-identical Cockpit copy.
The bounded V1 functional soak does not establish sustained performance budgets
or universal cross-platform/model execution.

## Local preview

Open `index.html` directly in any browser — no server needed.

## Structure

```
nirs4all-org/
├── index.html              # The entire landing page (HTML + CSS + JS)
├── release-status.html     # Manifest-driven, fail-closed release status
├── r1-archive.html         # Historical R1 consolidation from the baseline lock
├── r2-archive.html         # Historical R2 RC rollback from staging manifests
├── release-manifest.json   # Current source-only v2 projection of the selected lock
├── release-manifest-r2-history.json # Exact original v1 projection for R1/R2 history
├── native-candidate-staging.json # Immutable shared initial V1 publication receipt
├── scripts/                # Stdlib projection and static-site validation
├── tests/                  # Release-manifest negative tests
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

## Release manifest staging

Regenerate the public projection from an explicitly selected release lock:

```bash
python scripts/project_release_lock.py \
  --lock ../nirs4all-ecosystem/docs/contracts/release/aggregation-lock.n4a.lock.json \
  --output release-manifest.json
```

The v2 projector emits no downloads and makes no published/unpublished claim.
It admits only the declared seven source-owner identities and supported lock
schema/status values. The active lock remains aggregation-lock/v1; this does not
migrate that owner contract. Org 1.1.0 is a minor for the public projection wire
change. Retain the v1 history bytes, regenerate only the current endpoint after
selecting the actual canonical lock, and satisfy the version guard with the final
v1.1.0 tag through the normal maintainer release route. Run the full local gate before review:

```bash
python scripts/validate_site.py
python -m unittest discover -s tests -v
```

The immutable initial V1 snapshot was projected from exact governance/component
Git objects. Org and Cockpit copies remain byte-identical; the currently verified
SHA-256 is `83d90148cbb42bfd41b14a9dc68fe69e10a295ba0400edf1247c7c88b0d91ac3`.
Its original receipts remain historical and cannot be retargeted to a newer owner
cohort by changing labels or digests.

## Content

- **Hero**: Logo, tagline, install command, CTA buttons
- **Overview**: Python reference library vs Studio comparison
- **V1 topology**: `nirs4all-core` as the published portable aggregate,
  `web.nirs4all.org` as client-side-only/WASM, `nirs4all-ui` as the shared
  Studio/Web reusable components/assets package, and `nirs4all-providers` as the
  soft-importing read-side client layer over datasets and repository
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
