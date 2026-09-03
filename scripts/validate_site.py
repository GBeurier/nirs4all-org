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
    "commit": "091b8a0f3069e7a90167f78c81bb9d414c50ade5",
    "tree": "aebc80acdb0fb1c92425f744907f4d43ba251ec9",
    "ledger_sha256": "sha256:dc7a876a8c3240789b41c192ece6d4fe711d58babb7afb4621a7e75b63d04c55",
}
CANDIDATE_COMPONENTS = {
    "benchmarks": ("0.1.7", "9ff889a5be1bbc48a16d69a27ab743c23598f7da", "7c8b9c20cf8ae1c5d16a885ddc7c04f79aa1ed6b"),
    "core": ("0.3.28", "550cb8c80708e88ac7ebbc880acb4b82d8531632", "5181e3bc65c9a3ee413bdfc8b81f34cd61450f7e"),
    "dag_ml": ("0.3.23", "1caa26dc9b90f33bc3f53b15b4d85e18f3f67381", "8dffd6e823e214b720e1f8d715ddb7634bd4fb4e"),
    "dag_ml_data": ("0.2.10", "7d9b9fed04c135ed4c2bba472c782aca7ef85807", "42f02fdd723239cdbc933797e01d0d48b184712e"),
    "datasets": ("0.3.10", "007d7aafe50e6e4148d5a5cefe0ad96d9da37e7b", "7e37557cff5b4d825e9837e96cb4b2ff05211678"),
    "formats": ("0.2.9", "3e5a05674dfab4bbcebf23fe9d615d231ca4d551", "3b9717258fc80791d80641633a4bbf6478e7256a"),
    "io": ("0.1.14", "df7f2198862c71a24aeeba08ba09ee118524b55d", "16b2910ec602cfa4fd1db2f1c1d9b2a89893b857"),
    "methods": ("1.0.15", "e0bee1ce160cd805d3060185fd151c09230c3381", "7e4658658e37f77be18ef6d3d6aff150886efb5b"),
    "python": ("1.0.0rc2", "53a0acb964bff86dc67002763d8e9b850336731f", "2404b76783e9fc6e10723e671d274975e14756aa"),
    "studio": ("0.11.0", "ca4ee2afbb7596b2e4ba4b00f6d5797e553dfa39", "baa3b0b3aaf7c9aaa8a6331590e633f6aacee97c"),
    "tools": ("0.0.7", "88c2bc1e29603049cdbf1a1080a35845edf2f3c9", "d46a5fd2fcb7a2e14225cf1c3ad2661f7a4ab8b3"),
    "ui": ("0.1.13", "406d94d70004f27459ef12347af1e6f0079ab6ac", "377722160bbf188c474aacfecc8a6825095be2ca"),
    "web": ("0.1.10", "051bf636d7c1729087e5d40061b18bd690cd33b7", "e94251e350f31dbb996e1a2e477c466cfdf992ff"),
}
CANDIDATE_RELEASE_TRAIN = {
    "r1": (
        "0.13.0",
        "61a66d1bd0157dd9422facc4b32fca33989d4035",
        "e0583f7287c13ace028b38708268305626a47372",
        "0.10.1",
        "65b2aa2ac80249fdbd2fb0ccb55c82ac5b5e8219",
        "e978be82eca9df3cf44c721ea2692e6f0fc896c3",
        "legacy",
    ),
    "r2": (
        "1.0.0rc1",
        "1de9dcb50fcdcc6273113f54a7c7235528c31ed8",
        "97d348bf728144ec4324dcca6430d68eb3b9a1d5",
        "0.10.2",
        "54350c688ae576bbbb393c5a24dae8d106f77322",
        "9ecf2279039ef9b5af3d5be59be695f0dc0bc1d3",
        "native_with_explicit_legacy_opt_in",
    ),
    "r3": (
        "1.0.0rc2",
        "53a0acb964bff86dc67002763d8e9b850336731f",
        "2404b76783e9fc6e10723e671d274975e14756aa",
        "0.11.0",
        "ca4ee2afbb7596b2e4ba4b00f6d5797e553dfa39",
        "baa3b0b3aaf7c9aaa8a6331590e633f6aacee97c",
        "native_fail_closed_rust_only",
    ),
}
CANDIDATE_WORK_ITEM_STATES = {
    "API-001": "complete_local_code_release_hold",
    "API-004": "complete_local_native_full_transfer_plugin_finetune_refused",
    "API-005": "complete_local_by_executable_preflight_refusal",
    "CAP-001": "complete",
    "DAG-001": "complete_local_code_release_hold",
    "DOC-001": "complete_local_docs_release_hold",
    "GATE-001": "complete_local_linux_functional_release_hold",
    "INST-001": "prepared_local_linux_harness_external_matrix_hold",
    "PERF-002": "advanced_local_evidence_not_closed",
    "RC-001": "prepared_local_triage_external_evidence_hold",
    "REL-003": "complete_local_code_release_hold",
    "SEC-001": "prepared_local_native_fuzz_harnesses_campaign_not_closed",
    "SOAK-001": "advanced_local_evidence_not_closed",
    "STU-006": "complete_local_code_external_release_hold",
    "UI-001": "complete_registry_publication_downstream_product_hold",
    "WEB-001": "complete_local_code_release_hold",
    "WEBREL-001": "complete_local_staging_publication_hold",
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

    release_train = candidate.get("release_train")
    if not isinstance(release_train, dict) or (
        release_train.get("status") != "r1_r2_r3_distinct_candidates_r4_held"
        or release_train.get("publication") != "r1_published_r2_r3_unpublished"
    ):
        raise ValidationError("native candidate release train must retain only the published R1 receipt")
    milestones = release_train.get("milestones")
    if not isinstance(milestones, dict) or set(milestones) != {"r1", "r2", "r3", "r4"}:
        raise ValidationError("native candidate release milestones diverge")
    for milestone, expected in CANDIDATE_RELEASE_TRAIN.items():
        item = milestones.get(milestone)
        if not isinstance(item, dict):
            raise ValidationError(f"native candidate {milestone} milestone is missing")
        observed_milestone = (
            item.get("python_version"),
            item.get("python_commit"),
            item.get("python_tree"),
            item.get("studio_version"),
            item.get("studio_commit"),
            item.get("studio_tree"),
            item.get("default_engine"),
        )
        if observed_milestone != expected:
            raise ValidationError(f"native candidate {milestone} identities diverge")
    r1 = milestones["r1"]
    if (
        r1.get("publication") != "pypi_and_ghcr"
        or r1.get("publication_repair_commit") != "e76c834c75157f0c74fcbba7383a69a818ed6b34"
        or r1.get("publication_repair_tree") != "49dadfb76d6995c2ab825d8cb937a864ea773fb9"
        or r1.get("publication_workflow_run") != 33753479548
    ):
        raise ValidationError("native candidate R1 publication receipt diverges")
    if milestones["r4"] != {
        "python_version": "1.0.0",
        "status": "not_created_until_stable_gates_are_green",
    }:
        raise ValidationError("R4 must remain absent until stable gates are green")

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
        raise ValidationError("native candidate identities diverge from Governance 091b8a0")
    benchmarks = next(component for component in components if component.get("key") == "benchmarks")
    if benchmarks.get("qualification") != "selected_heads_unmeasured_historical_measurement_retained_release_no_go":
        raise ValidationError("stale Bench report must not be exposed as current evidence")

    cutover = candidate.get("cutover_observability")
    expected_cutover = {
        "work_item": "CUT-002",
        "legacy_activation": "explicit_legacy_or_dual_only",
        "warning_format": "stable_structured_json",
        "counter_scope": "opt_in_process_local_non_persistent_intentional",
        "counter_opt_in": True,
        "strict_paths_silent": True,
        "implicit_fallback": False,
        "evidence_commit": "b652bba3bc903f20854a3bba65a41aefc42eb2eb",
    }
    if cutover != expected_cutover:
        raise ValidationError("native candidate CUT-002 evidence diverges")

    governance = candidate.get("governance")
    expected_governance = {
        "capability_inventory": {
            "commit": "cf6cd1d96c12d7043134ab0a7b4f593e19ec553b",
            "tree": "77aa215ba6caad62fb114d6c7d6d9879569a48e6",
            "status": "exhaustive_candidate_inventory_complete_no_go",
        },
        "ownership": {
            "commit": "fe17a3f939f9fb95c8ed1e068138c72ceac92890",
            "tree": "f3c849628f4711d8590d3d73c33af877f9cf49ab",
            "status": "lanes_and_handoffs_complete_local",
        },
    }
    if governance != expected_governance:
        raise ValidationError("native candidate governance evidence diverges")

    performance = candidate.get("performance")
    if not isinstance(performance, dict) or (
        performance.get("evidence_mode") != "stale_not_current_evidence"
        or performance.get("contract") != "archive_v2_same_matrix_four_surfaces"
        or performance.get("budgets_frozen") is not False
        or performance.get("release_eligible") is not False
        or performance.get("refresh_required") is not True
        or performance.get("report_scope") != "predates_distinct_r1_r2_r3_candidates"
        or performance.get("timings_ms") is not None
    ):
        raise ValidationError("stale Bench report must not be accepted as current performance evidence")
    if candidate.get("work_item_states") != CANDIDATE_WORK_ITEM_STATES:
        raise ValidationError("selected work-item states are incomplete or overclaimed")

    security = candidate.get("security_harnesses")
    if not isinstance(security, dict) or security.get("work_item") != "SEC-001":
        raise ValidationError("SEC-001 harness evidence is missing")
    if security.get("evidence_status") != "four_native_targets_prepared_campaign_not_run":
        raise ValidationError("SEC-001 must remain prepared with no fuzz campaign")
    expected_harnesses = {
        "formats": ("892a48b38f6c94697f805524f6efd4e8ff7323b0", "28e9adc8dcae49c58a0e5585dcacb821a8006f58", "registry_open_bytes", 1048576),
        "core": ("0218bfc8b9d9193f771d27470e7cf9d5cf578823", "0d2537d715bed3d5fd60c836f71e5a8fd041ac8b", "archive_v2_bytes", 2097152),
        "methods": ("530b11c632ac467e6bf54022c7241d27cd72d73c", "fc4c47d6f07ad01ac52da4d19f715f2c61b968e7", "n4m_fuzz_n4mm_driver", 1048576),
        "studio_store": ("6d53f301830947ff85767c53c800829741af75ff", "3ae8f218a3c7eef23345ccc1630f29aa89594c2e", "workspace_store_v5_bytes", 2097152),
    }
    observed_harnesses = {
        item.get("surface"): (item.get("commit"), item.get("tree"), item.get("target"), item.get("input_limit_bytes"))
        for item in security.get("harnesses", [])
        if isinstance(item, dict)
    }
    if observed_harnesses != expected_harnesses:
        raise ValidationError("SEC-001 prepared harness identities diverge")
    release_limit = security.get("release_limit")
    if not isinstance(release_limit, str) or "no fuzz campaign has run" not in release_limit:
        raise ValidationError("SEC-001 open campaign hold is missing")

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
    if not {"qualified_local", "qualified_bounded", "not_qualified", "stale_not_current_evidence"}.issubset(statuses):
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
        "Candidat produit NO-GO — composants natifs et Web publiés",
        "native-candidate-staging.json",
        "Train R1/R2/R3 distinct",
        "Capability matrix qualifiée",
        "Codes 0/10/20",
        "CUT-002",
        "Performance · preuve à rafraîchir",
        "Gouvernance du candidat",
        "États finaux locaux",
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


def validate_r1_archive_page(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    required = (
        "Archive historique · consolidation R1",
        "release-manifest.json",
        "lock canonique baseline",
        "elle ne décrit pas le backend natif comme défaut",
        "release-status.html#migration-title",
        "https://methods.nirs4all.org/",
        "component.publication.state === 'pending'",
        "component.publication.artifacts.length === 0",
        'aria-live="polite"',
    )
    for marker in required:
        if marker not in text:
            raise ValidationError(f"r1-archive.html: missing {marker!r}")
    if "native-candidate-staging.json" in text:
        raise ValidationError("r1-archive.html must not derive identities from the native candidate")
    if re.search(r"\bv?\d+\.\d+\.\d+\b", text):
        raise ValidationError("r1-archive.html hard-codes a release version")
    if re.search(r"\b[0-9a-f]{40}\b", text):
        raise ValidationError("r1-archive.html hard-codes a commit SHA")
    for forbidden in ("releases/latest", "browser_download_url", "pypi.org/project", "npmjs.com/package"):
        if forbidden in text:
            raise ValidationError(f"r1-archive.html exposes an artifact or registry path: {forbidden}")


def validate_r2_archive_page(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    required = (
        "Archive historique · profil de rollback R2",
        "RC R2 native-default, legacy opt-in",
        "release-manifest.json",
        "native-candidate-staging.json",
        "release-status.html#migration-title",
        "https://methods.nirs4all.org/",
        "r1-archive.html",
        "component.publication === 'unavailable'",
        "component.artifacts.length === 0",
        "component.registry_urls.length === 0",
        "implicit_fallback === false",
        'aria-live="polite"',
    )
    for marker in required:
        if marker not in text:
            raise ValidationError(f"r2-archive.html: missing {marker!r}")
    if re.search(r"\bv?\d+\.\d+\.\d+\b", text):
        raise ValidationError("r2-archive.html hard-codes a release version")
    if re.search(r"\b[0-9a-f]{40}\b", text):
        raise ValidationError("r2-archive.html hard-codes a commit SHA")
    for forbidden in ("releases/latest", "browser_download_url", "pypi.org/project", "npmjs.com/package"):
        if forbidden in text:
            raise ValidationError(f"r2-archive.html exposes an artifact or registry path: {forbidden}")


def validate_sitemap() -> None:
    tree = ET.parse(ROOT / "sitemap.xml")
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = {element.text for element in tree.findall(".//sm:loc", namespace)}
    expected = {
        f"{SITE_ORIGIN}/",
        f"{SITE_ORIGIN}/open-source-nirs-tools.html",
        f"{SITE_ORIGIN}/release-status.html",
        f"{SITE_ORIGIN}/r1-archive.html",
        f"{SITE_ORIGIN}/r2-archive.html",
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
        validate_r1_archive_page(ROOT / "r1-archive.html")
        validate_r2_archive_page(ROOT / "r2-archive.html")
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
