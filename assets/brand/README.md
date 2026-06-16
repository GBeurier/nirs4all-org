# nirs4all / dag-ml brand kit

Generated logo assets for every package in the nirs4all + dag-ml ecosystems.
Built from the source marks in [`../_chart/`](../_chart/) following the rules in
[`../_chart/Logos.txt`](../_chart/Logos.txt).

All SVGs are **self-contained**: text is converted to outlines (Inter SemiBold /
Bold), so they render identically everywhere with no web-font dependency.

## Layout

```
brand/
├── ecosystem/                  ← umbrella marks (rich emblem + wordmark)
│   ├── nirs4all_horizontal.svg/.png      nirs4all  (nirs black · 4 red · all teal)
│   ├── nirs4all_stacked.svg/.png
│   ├── dag-ml_horizontal.svg/.png        DAG-ML    (DAG- navy · ML teal)
│   ├── dag-ml_stacked.svg/.png
│   └── *-dark.svg                        on-dark variants
└── <package>/                  ← one folder per package
    ├── icon.svg                square app/brand mark, recolored
    ├── icon-512/256/180/32.png raster sizes (180 = apple-touch)
    ├── favicon.ico             multi-size (16–256)
    ├── horizontal.svg/.png     icon + "nirs4all-<pkg>" wordmark
    ├── horizontal-dark.svg     on-dark variant
    ├── stacked.svg/.png        icon over the n4X lettermark
    ├── stacked-dark.svg        on-dark variant
    └── og.png                  1200×630 social card
```

## Packages & colors

| key | color | n4X | wordmark |
|---|---|---|---|
| `nirs4all` (lib) | teal `#058E96` | n4a | nirs·4·all |
| `nirs4all-studio` | `#96C800` | n4s | nirs4all-studio |
| `nirs4all-lite` | `#E9362D` | n4l | nirs4all-lite |
| `nirs4all-web` | `#FF6400` | n4w | nirs4all-web |
| `nirs4all-datasets` | `#FFBE00` | n4d | nirs4all-datasets |
| `nirs4all-methods` | `#00A5D2` | n4m | nirs4all-methods |
| `nirs4all-io` | `#CC99FF` | n4i | nirs4all-io |
| `nirs4all-formats` | `#6732B9` | n4f | nirs4all-formats |
| `nirs4all-benchmarks` | `#00704A` | n4b | nirs4all-benchmarks |
| `nirs4all-repository` | `#AC564A` | n4r | nirs4all-repository |
| `nirs4all-papers` | `#767171` | n4p | nirs4all-papers |
| `nirs4all-cluster` | `#1B5789` | n4c | nirs4all-cluster |
| `dag-ml` | teal `#058E96` | DM | DAG-ML |
| `dag-ml-data` | yellow `#FFBE00` | DMd | DAG-ML-data |

Constant accents: the **4** / **-** is always red `#E9362D`; package-suffix text is
black `#000000` (white in `-dark` variants).

## Color rules (from Logos.txt)

- **Icon** — the square mark recolored to the package color (nirs4all spectra wave,
  dag-ml `{ }` braces), white content.
- **Horizontal** — `nirs`(package color) · `4`(red) · `all-<pkg>`(black). The
  umbrella `nirs4all` mark uses `nirs`(black) · `4`(red) · `all`(teal).
- **Stacked** — icon above `n4X`: `n`(black) · `4`(red) · `X`(package color), where
  X is the package initial (`a` for the Python lib). dag-ml uses `DM` / `DMd`
  (`D`=navy · `M`=teal · `d`=package color).

## Regenerating

Tooling lives in `../_chart/build/` (git-ignored): a Python venv with
`cairosvg` + `fonttools` and the Inter variable font.

```bash
cd ../_chart/build && .venv/bin/python gen.py
```
