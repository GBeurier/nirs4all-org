#!/usr/bin/env python3
"""Validate the hand-authored site and its fail-closed release surface."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SITE_ORIGIN = "https://nirs4all.org"
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "/home/",
    "/dev/shm/",
    "_worktrees",
    "selected_workspace_path",
    "localhost",
    "127.0.0.1",
)
CANDIDATE_SOURCE = {
    "commit": "a3ea904799b84977bc3e5661a27799e7078f8430",
    "tree": "b240b3dfcf0758dd31dc1fc743384d82122c145d",
    "ledger_sha256": "sha256:bf588aa87d10329aa1e96c0249583e0c432053f8ceec06cd7d8ffdb6460be8de",
}
CANDIDATE_COMPONENTS = {
    "benchmarks": ("0.1.6", "433ad714d475dd0c8fd7d4ee2664665894caaee9", "4103609587714f1a19c6834c2e4bbf2d71ea4d97"),
    "core": ("0.3.25", "6b25b63bb09adfe3c4dae8ffacc90d09a1a81e16", "11344243884a24aeec75f73e0469f23721c76978"),
    "dag_ml": ("0.3.23", "dafb8b6fb98f9d380d30559a3f4b868c91e5b5c4", "44a2c4a46911d2c49c33fe75418674bd0e129d5e"),
    "dag_ml_data": ("0.2.10", "1f60b920d34acda7c0fbc044b593bb6af1fab4c1", "f2144d861642e81758dcef4f6ee76ec32c0961ff"),
    "datasets": ("0.3.9", "53017672c82df106a17b512846425bc9e846565f", "68513f3b938407846a9014d0dad47f58ded09bf4"),
    "formats": ("0.2.8", "2d46285843dc366da1d38f133131b5329c886b12", "2ee12c035db8a78721315ee65cf684d811552aa9"),
    "io": ("0.1.12", "54fa4f5f544f08f37317897612f78e4ee103b5a4", "c583ba2e8d2fec5376933086d4fbb765c931486f"),
    "methods": ("1.0.15", "48ad1e5a50844f68c2b99e93b02ad6a3b491c07b", "f2eaa3c46629c26d11913a25bff723f9a9cefbc9"),
    "python": ("0.10.3", "56db62c176e77afe8650b71aefb5988c0d172f87", "abd855244a1b4a4e818ec3f3bcce500417f440c3"),
    "studio": ("0.9.1", "2ad862aeab4048ced6c4c70fee5b2f88adaa16e8", "e32f15cd1c4e76ef9fb82d2c2ffc81afddc6bbdc"),
    "tools": ("0.0.7", "e3a332633f87b4652a06f8993e63c386a3568698", "c708b9153be8bfd85ba02135c1406f3f3ddf1ae2"),
    "web": ("0.1.8", "20867a71c45731f757267a98e7928710e7c3693d", "5883040939306b8d5ef5a02eacde90caeea23efa"),
}


class ValidationError(ValueError):
    """Raised for a release manifest or static-site contract violation."""


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str], int]] = []
        self.ids: list[str] = []
        self.links: list[tuple[str, int]] = []
        self.lang: str | None = None
        self.title_parts: list[str] = []
        self.in_title = False
        self.json_ld_parts: list[list[str]] = []
        self._json_ld: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        self.tags.append((tag, values, self.getpos()[0]))
        if tag == "html":
            self.lang = values.get("lang")
        if "id" in values:
            self.ids.append(values["id"])
        for key in ("href", "src"):
            if values.get(key):
                self.links.append((values[key], self.getpos()[0]))
        if tag == "title":
            self.in_title = True
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json_ld = []
            self.json_ld_parts.append(self._json_ld)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        if tag == "script" and self._json_ld is not None:
            self._json_ld = None

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self._json_ld is not None:
            self._json_ld.append(data)


def _exact_keys(value: dict[str, Any], expected: set[str], where: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ValidationError(
            f"{where}: expected keys {sorted(expected)}, got {sorted(actual)}"
        )


def validate_release_manifest(manifest: Any) -> None:
    if not isinstance(manifest, dict):
        raise ValidationError("release manifest must be an object")
    _exact_keys(
        manifest,
        {"schema_version", "source_lock", "release_train", "components"},
        "manifest",
    )
    if manifest["schema_version"] != "n4a.org-release-manifest/v1":
        raise ValidationError("unsupported release-manifest schema")

    source = manifest["source_lock"]
    if not isinstance(source, dict):
        raise ValidationError("source_lock must be an object")
    _exact_keys(
        source,
        {
            "aggregation_lock_version",
            "manifest_digest",
            "lock_sha256",
            "repository_url",
            "path",
        },
        "source_lock",
    )
    if source["aggregation_lock_version"] != 1:
        raise ValidationError("source_lock version must be 1")
    if not SHA256_RE.fullmatch(source["manifest_digest"] or ""):
        raise ValidationError("invalid source manifest digest")
    if not SHA256_RE.fullmatch(source["lock_sha256"] or ""):
        raise ValidationError("invalid source lock digest")
    if source["repository_url"] != "https://github.com/GBeurier/nirs4all-ecosystem":
        raise ValidationError("unexpected source-lock repository")
    if source["path"] != "docs/contracts/release/aggregation-lock.n4a.lock.json":
        raise ValidationError("unexpected source-lock path")

    train = manifest["release_train"]
    if not isinstance(train, dict):
        raise ValidationError("release_train must be an object")
    _exact_keys(train, {"milestone", "state", "published", "message"}, "release_train")
    if train != {
        "milestone": "R2",
        "state": "in_progress",
        "published": False,
        "message": "Publication en cours — le jalon R2 reste incomplet.",
    }:
        raise ValidationError("public milestone must remain the incomplete R2 train")

    components = manifest["components"]
    if not isinstance(components, list) or not components:
        raise ValidationError("components must be a non-empty array")
    seen: set[str] = set()
    for index, component in enumerate(components):
        where = f"components[{index}]"
        if not isinstance(component, dict):
            raise ValidationError(f"{where} must be an object")
        _exact_keys(
            component,
            {"id", "name", "repository_url", "version", "commit_sha", "publication"},
            where,
        )
        component_id = component["id"]
        if not isinstance(component_id, str) or not re.fullmatch(
            r"[a-z][a-z0-9_]*", component_id
        ):
            raise ValidationError(f"{where}: invalid id")
        if component_id in seen:
            raise ValidationError(f"{where}: duplicate id")
        seen.add(component_id)
        if not isinstance(component["name"], str) or not component["name"]:
            raise ValidationError(f"{where}: invalid name")
        if not re.fullmatch(
            r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",
            component["repository_url"] or "",
        ):
            raise ValidationError(f"{where}: repository must be a public GitHub URL")
        if not VERSION_RE.fullmatch(component["version"] or ""):
            raise ValidationError(f"{where}: invalid version")
        if not COMMIT_RE.fullmatch(component["commit_sha"] or ""):
            raise ValidationError(f"{where}: invalid commit SHA")

        publication = component["publication"]
        if not isinstance(publication, dict):
            raise ValidationError(f"{where}.publication must be an object")
        _exact_keys(publication, {"state", "artifacts"}, f"{where}.publication")
        if publication["state"] not in {"pending", "published"}:
            raise ValidationError(f"{where}: invalid publication state")
        artifacts = publication["artifacts"]
        if not isinstance(artifacts, list):
            raise ValidationError(f"{where}: artifacts must be an array")
        if publication["state"] == "pending" and artifacts:
            raise ValidationError(f"{where}: pending component cannot expose artifacts")
        if publication["state"] == "published" and not artifacts:
            raise ValidationError(f"{where}: published component requires artifacts")
        for artifact_index, artifact in enumerate(artifacts):
            artifact_where = f"{where}.artifacts[{artifact_index}]"
            if not isinstance(artifact, dict):
                raise ValidationError(f"{artifact_where} must be an object")
            _exact_keys(artifact, {"name", "url", "sha256"}, artifact_where)
            if not isinstance(artifact["name"], str) or not artifact["name"]:
                raise ValidationError(f"{artifact_where}: invalid name")
            if not isinstance(artifact["url"], str) or not artifact["url"].startswith(
                "https://"
            ):
                raise ValidationError(f"{artifact_where}: artifact URL must use HTTPS")
            if not SHA256_RE.fullmatch(artifact["sha256"] or ""):
                raise ValidationError(f"{artifact_where}: invalid SHA-256")

    serialized = json.dumps(manifest, ensure_ascii=False)
    for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
        if fragment.lower() in serialized.lower():
                raise ValidationError(
                    f"public manifest leaks forbidden fragment: {fragment}"
                )


def validate_native_candidate(candidate: Any) -> None:
    """Validate the exact unpublished candidate shared with Cockpit."""
    if not isinstance(candidate, dict) or candidate.get("schema_version") != "n4a.native-candidate-staging/v1":
        raise ValidationError("unsupported native candidate schema")
    source = candidate.get("source")
    if not isinstance(source, dict):
        raise ValidationError("native candidate source is missing")
    for key, expected in CANDIDATE_SOURCE.items():
        if source.get(key) != expected:
            raise ValidationError(f"native candidate source {key} diverges")
    if source.get("repository_url") != "https://github.com/GBeurier/nirs4all-ecosystem" or source.get("ledger_path") != "docs/contracts/release/migration-work-ledger.yaml":
        raise ValidationError("native candidate source is not the governance ledger")

    release = candidate.get("release")
    if not isinstance(release, dict) or release.get("status") != "no_go" or release.get("publication") != "unpublished":
        raise ValidationError("native candidate must remain NO-GO and unpublished")
    for field in ("canonical_lock_updated", "downloads_enabled", "registry_links_enabled"):
        if release.get(field) is not False:
            raise ValidationError(f"native candidate must keep {field}=false")

    components = candidate.get("components")
    if not isinstance(components, list):
        raise ValidationError("native candidate components are missing")
    observed: dict[str, tuple[str, str, str]] = {}
    for component in components:
        if not isinstance(component, dict) or not isinstance(component.get("key"), str):
            raise ValidationError("invalid native candidate component")
        key = component["key"]
        if key in observed:
            raise ValidationError(f"duplicate native candidate component: {key}")
        observed[key] = (component.get("version"), component.get("commit"), component.get("tree"))
        if component.get("publication") != "unavailable" or component.get("artifacts") != [] or component.get("registry_urls") != []:
            raise ValidationError(f"{key}: unpublished candidate exposes publication evidence")
        if not re.fullmatch(r"https://github\.com/GBeurier/[A-Za-z0-9_.-]+", component.get("repository_url", "")):
            raise ValidationError(f"{key}: unsafe candidate repository URL")
    if observed != CANDIDATE_COMPONENTS:
        raise ValidationError("native candidate identities diverge from a3ea9047")

    architecture = candidate.get("architecture")
    if not isinstance(architecture, dict) or architecture.get("studio_control_plane") != "rust_only" or architecture.get("embedded_cpython") != "bounded_attested_stdio_library_plugin_host":
        raise ValidationError("native candidate architecture boundary diverges")
    forbidden_roles = set(architecture.get("python_forbidden_roles", []))
    if forbidden_roles != {"http_server", "scheduler", "store", "listener", "fallback"}:
        raise ValidationError("native candidate Python forbidden roles diverge")

    migration = candidate.get("migration")
    if not isinstance(migration, dict) or migration.get("version") != "0.0.7":
        raise ValidationError("native candidate migration tool diverges")
    if [item.get("code") for item in migration.get("exit_codes", []) if isinstance(item, dict)] != [0, 10, 20]:
        raise ValidationError("native candidate migration codes diverge")
    docs = candidate.get("methods_documentation")
    if not isinstance(docs, dict) or docs.get("mapped_pages") != "209/209" or docs.get("bibliography_entries") != 88:
        raise ValidationError("Methods scientific documentation evidence diverges")
    capabilities = candidate.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise ValidationError("native candidate capability matrix is missing")
    statuses = {entry.get("status") for entry in capabilities if isinstance(entry, dict)}
    if not {"qualified_local", "qualified_bounded", "not_qualified", "fixture_only"}.issubset(statuses):
        raise ValidationError("native candidate capability limits are incomplete")

    serialized = json.dumps(candidate, ensure_ascii=False).lower()
    for fragment in (*FORBIDDEN_PUBLIC_FRAGMENTS, "browser_download_url"):
        if fragment.lower() in serialized:
            raise ValidationError(f"native candidate leaks forbidden fragment: {fragment}")


def _local_target(url: str) -> tuple[Path, str] | None:
    parsed = urlsplit(url)
    if parsed.scheme in {"mailto", "tel", "data", "javascript"}:
        return None
    if parsed.scheme or parsed.netloc:
        if f"{parsed.scheme}://{parsed.netloc}" != SITE_ORIGIN:
            return None
    path = unquote(parsed.path)
    if not path or path == "/":
        path = "index.html"
    elif path.startswith("/"):
        path = path[1:]
    target = ROOT / path
    if target.is_dir():
        target /= "index.html"
    return target, parsed.fragment


def parse_document(path: Path) -> DocumentParser:
    parser = DocumentParser()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


def validate_document(path: Path, parser: DocumentParser) -> None:
    rel = path.relative_to(ROOT)
    if not parser.lang:
        raise ValidationError(f"{rel}: html[lang] is required")
    if not "".join(parser.title_parts).strip():
        raise ValidationError(f"{rel}: non-empty title is required")
    tags = parser.tags
    if sum(tag == "main" for tag, _, _ in tags) != 1:
        raise ValidationError(f"{rel}: exactly one main element is required")
    if sum(tag == "h1" for tag, _, _ in tags) != 1:
        raise ValidationError(f"{rel}: exactly one h1 is required")
    descriptions = [
        attrs.get("content", "")
        for tag, attrs, _ in tags
        if tag == "meta" and attrs.get("name") == "description"
    ]
    if len(descriptions) != 1 or not descriptions[0]:
        raise ValidationError(f"{rel}: exactly one meta description is required")
    canonicals = [
        attrs.get("href", "")
        for tag, attrs, _ in tags
        if tag == "link" and attrs.get("rel") == "canonical"
    ]
    if len(canonicals) != 1 or not canonicals[0].startswith(SITE_ORIGIN):
        raise ValidationError(f"{rel}: exactly one canonical nirs4all URL is required")
    if len(parser.ids) != len(set(parser.ids)):
        raise ValidationError(f"{rel}: duplicate id")
    if not parser.json_ld_parts:
        raise ValidationError(f"{rel}: JSON-LD is required")
    for parts in parser.json_ld_parts:
        try:
            value = json.loads("".join(parts))
        except json.JSONDecodeError as exc:
            raise ValidationError(f"{rel}: invalid JSON-LD: {exc}") from exc
        if not isinstance(value, dict) or value.get("@context") != "https://schema.org":
            raise ValidationError(f"{rel}: JSON-LD must use schema.org")

    for tag, attrs, line in tags:
        if tag == "img" and "alt" not in attrs:
            raise ValidationError(f"{rel}:{line}: img requires alt")
    for url, line in parser.links:
        target = (path, url[1:]) if url.startswith("#") else _local_target(url)
        if target is None:
            continue
        target_path, fragment = target
        if not target_path.is_file():
            raise ValidationError(f"{rel}:{line}: missing internal target {url}")
        if fragment and target_path.suffix == ".html":
            target_parser = parse_document(target_path)
            if fragment not in set(target_parser.ids):
                raise ValidationError(f"{rel}:{line}: missing anchor {url}")


def validate_release_page(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    required = (
        "Publication en cours — candidat local NO-GO",
        "native-candidate-staging.json",
        "Capability matrix qualifiée",
        "Codes 0/10/20",
        'aria-live="polite"',
    )
    for marker in required:
        if marker not in text:
            raise ValidationError(f"release-status.html: missing {marker!r}")
    if re.search(r"\bv?\d+\.\d+\.\d+\b", text):
        raise ValidationError("release-status.html hard-codes a release version")
    if re.search(r"\b[0-9a-f]{40}\b", text):
        raise ValidationError("release-status.html hard-codes a commit SHA")
    for forbidden in (
        "nirs4all-core/releases/latest",
        "pypi.org/project/nirs4all-core",
        "crates.io/crates/nirs4all",
        "npmjs.com/package/nirs4all",
    ):
        if forbidden in text:
            raise ValidationError(f"release-status.html bypasses manifest: {forbidden}")


def validate_sitemap() -> None:
    tree = ET.parse(ROOT / "sitemap.xml")
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = {element.text for element in tree.findall(".//sm:loc", namespace)}
    expected = {
        f"{SITE_ORIGIN}/",
        f"{SITE_ORIGIN}/open-source-nirs-tools.html",
        f"{SITE_ORIGIN}/release-status.html",
    }
    if not expected.issubset(urls):
        raise ValidationError(f"sitemap missing URLs: {sorted(expected - urls)}")
    for url in urls:
        if url and url.startswith(SITE_ORIGIN):
            target = _local_target(url)
            if target is not None and not target[0].is_file():
                raise ValidationError(f"sitemap target does not exist: {url}")

    index_tree = ET.parse(ROOT / "sitemap-index.xml")
    index_namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    indexed_sitemaps = {
        element.text for element in index_tree.findall(".//sm:loc", index_namespace)
    }
    if f"{SITE_ORIGIN}/sitemap.xml" not in indexed_sitemaps:
        raise ValidationError("sitemap-index.xml does not reference the site sitemap")

    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    for sitemap_url in (
        f"{SITE_ORIGIN}/sitemap-index.xml",
        f"{SITE_ORIGIN}/sitemap.xml",
    ):
        if f"Sitemap: {sitemap_url}" not in robots:
            raise ValidationError(f"robots.txt missing {sitemap_url}")


def main() -> int:
    try:
        manifest = json.loads(
            (ROOT / "release-manifest.json").read_text(encoding="utf-8")
        )
        validate_release_manifest(manifest)
        candidate = json.loads(
            (ROOT / "native-candidate-staging.json").read_text(encoding="utf-8")
        )
        validate_native_candidate(candidate)
        for path in sorted(ROOT.glob("*.html")):
            validate_document(path, parse_document(path))
        validate_release_page(ROOT / "release-status.html")
        validate_sitemap()
    except (OSError, json.JSONDecodeError, ET.ParseError, ValidationError) as exc:
        print(f"site validation failed: {exc}", file=sys.stderr)
        return 1
    print(
        "site validation passed: lock baseline, native candidate, HTML, links, accessibility, SEO, JSON-LD, sitemap"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
