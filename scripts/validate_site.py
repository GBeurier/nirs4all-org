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
    "commit": "d7d62825e5aa5ab5554ec7d084fab29be66acd74",
    "tree": "52316e7150f6a778b3982a1aef5fc7627389f8b4",
    "ledger_sha256": "sha256:d7fec320b6906c192bd7388f3137436ab8875e135f440ce1461c89379b537450",
}
CANDIDATE_COMPONENTS = {
    "benchmarks": ("0.1.7", "1649cdfb253a0eb0efec2c15b5e21a5c6219dc80", "f577ae2459266dacfa0dace1ec185409344c12c9"),
    "core": ("0.3.28", "550cb8c80708e88ac7ebbc880acb4b82d8531632", "5181e3bc65c9a3ee413bdfc8b81f34cd61450f7e"),
    "dag_ml": ("0.3.23", "1caa26dc9b90f33bc3f53b15b4d85e18f3f67381", "8dffd6e823e214b720e1f8d715ddb7634bd4fb4e"),
    "dag_ml_data": ("0.2.10", "7d9b9fed04c135ed4c2bba472c782aca7ef85807", "42f02fdd723239cdbc933797e01d0d48b184712e"),
    "datasets": ("0.3.10", "007d7aafe50e6e4148d5a5cefe0ad96d9da37e7b", "7e37557cff5b4d825e9837e96cb4b2ff05211678"),
    "formats": ("0.2.9", "3e5a05674dfab4bbcebf23fe9d615d231ca4d551", "3b9717258fc80791d80641633a4bbf6478e7256a"),
    "io": ("0.1.14", "df7f2198862c71a24aeeba08ba09ee118524b55d", "16b2910ec602cfa4fd1db2f1c1d9b2a89893b857"),
    "methods": ("1.0.16", "49aa40e90afef676f25809db1bd2a523e9582a49", "03de9a3f0b116b4d4c7446acc6cd1e4bf8814a83"),
    "providers": ("0.2.11", "b2210ec717c0de0055fc8b9424b115a933efdb4e", "23a4a70513a33118c19923a47647a0a362c85f18"),
    "python": ("1.0.0", "a5e5f93b8b1336bc58c0a23814066e5e14678d12", "1f566f81f5309ed0b73872fbc01db00a40d4e3e2"),
    "repository": ("0.1.12", "dbd9dae1205e1905692decd9fc7243f4fbda3068", "c37878a2f83baf90fcfb222944d4d06178164a71"),
    "studio": ("0.11.0", "1c36b93f62cf560d8f4822c76cfe09fbb1d0e67b", "e6bdb63b994a276336e976d5b0a37904abc87731"),
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
        "d351785dbc17290cdc85a797ead299ffce58f257",
        "364c9e63a0ef667c62e8d7223af632c5783b880a",
        "0.10.2",
        "54350c688ae576bbbb393c5a24dae8d106f77322",
        "9ecf2279039ef9b5af3d5be59be695f0dc0bc1d3",
        "native_with_explicit_legacy_opt_in",
    ),
    "r3": (
        "1.0.0rc2",
        "3567bd4abcaa64443a1946748a579f0803e91889",
        "a06c4015a26124df1e529f82108ee7bd115236cb",
        "0.11.0",
        "1c36b93f62cf560d8f4822c76cfe09fbb1d0e67b",
        "e6bdb63b994a276336e976d5b0a37904abc87731",
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
    "INST-001": "complete_with_bounded_windows_installed_path_waiver",
    "PERF-002": "complete_v1_bounded_measurement_sustained_budgets_deferred_post_v1",
    "RC-001": "complete_existing_evidence_reconciled",
    "REL-003": "complete_local_code_release_hold",
    "ROB-001": "complete_local_functional_non_crash_non_blocking",
    "SOAK-001": "complete_functional_campaign_passed",
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
    """Validate the exact release projection shared with Cockpit."""
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
    if not isinstance(release, dict) or release.get("status") != "go" or release.get("publication") != "published":
        raise ValidationError("native release must remain GO and published")
    if release.get("canonical_lock_updated") is not False:
        raise ValidationError("native release projection must precede the immutable lock tag")
    for field in ("downloads_enabled", "registry_links_enabled"):
        if release.get(field) is not True:
            raise ValidationError(f"native release must keep {field}=true")

    release_train = candidate.get("release_train")
    if not isinstance(release_train, dict) or (
        release_train.get("status") != "r1_r2_r3_r4_distinct_published_releases"
        or release_train.get("publication") != "python_r1_r2_r3_r4_and_studio_published"
    ):
        raise ValidationError("native release train must retain all published receipts")
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
    for milestone, expected_run in {"r2": 33868949671, "r3": 33873060692}.items():
        receipt = milestones[milestone]
        if (
            receipt.get("publication") != "pypi_and_ghcr"
            or receipt.get("publication_workflow_run") != expected_run
            or not isinstance(receipt.get("release_id"), int)
            or not COMMIT_RE.fullmatch(receipt.get("tag_object", ""))
            or any(
                not re.fullmatch(r"[0-9a-f]{64}", receipt.get(field, ""))
                for field in ("wheel_sha256", "sdist_sha256", "record_sha256", "installed_manifest_sha256")
            )
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", receipt.get("ghcr_oci_index", ""))
        ):
            raise ValidationError(f"native candidate {milestone.upper()} publication receipt diverges")
    expected_r4 = {
        "documentation_commit": "ef39f1a53dd120b9ce28907dc372d755dd621430",
        "documentation_tree": "126dfe87557a265d2a6c7894885c7772604d5311",
        "python_commit": "a5e5f93b8b1336bc58c0a23814066e5e14678d12",
        "python_tree": "1f566f81f5309ed0b73872fbc01db00a40d4e3e2",
        "python_version": "1.0.0",
        "status": "published_pypi_and_ghcr_release_workflow_green",
        "publication": "pypi_and_ghcr",
        "publication_workflow_run": 33885659321,
        "release_id": 382803888,
        "release_url": "https://github.com/GBeurier/nirs4all/releases/tag/1.0.0",
        "tag_object": "a1fc8123e03840624f459b0078fdf104955c7800",
        "wheel_sha256": "fb02ef000368f9d46c228214d2c8e19f71b6b6cf52cb1d52fd66b9220be1d002",
        "sdist_sha256": "11feaca3b442c536e0baf0db58209c62cd76c180af2e2b229b270fd31ae06f59",
        "record_sha256": "6c1b938ec4b26f83e998de60d446648d9e013a56f39ce89b11312b301246e736",
        "installed_manifest_sha256": "caa89ad16dd77a4528f80965e66a03fed71101a4cf5cedb1fcd15a79c60be7ee",
        "ghcr_oci_index": "sha256:c0a7420e1c63fc8bef403c673aefc46f62dc86cff45d28dff9b2e9c96f60ed9e",
    }
    if milestones["r4"] != expected_r4:
        raise ValidationError("R4 published receipt diverges")

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
        if key == "methods":
            expected_artifact_ids = {"source_tarball", "sbom", "matlab_octave", "r_n4m", "r_pls4all"}
            if (
                component.get("publication") != "published"
                or {artifact.get("id") for artifact in component.get("artifacts", [])} != expected_artifact_ids
                or len(component.get("registry_urls", [])) != 4
            ):
                raise ValidationError("methods: published multi-registry receipt is incomplete")
            for artifact in component["artifacts"]:
                if (
                    not isinstance(artifact.get("filename"), str)
                    or not re.fullmatch(r"[0-9a-f]{64}", artifact.get("sha256", ""))
                    or not isinstance(artifact.get("size"), int)
                    or artifact["size"] <= 0
                ):
                    raise ValidationError("methods: malformed artifact receipt")
            if any(not registry_url.startswith("https://") for registry_url in component["registry_urls"]):
                raise ValidationError("methods: malformed registry receipt URL")
        elif key in {"providers", "repository"}:
            if component.get("publication") != "published" or len(component.get("artifacts", [])) != 2:
                raise ValidationError(f"{key}: published receipt is incomplete")
            for artifact in component["artifacts"]:
                if (
                    artifact.get("id") not in {"wheel", "sdist"}
                    or not isinstance(artifact.get("filename"), str)
                    or not re.fullmatch(r"[0-9a-f]{64}", artifact.get("sha256", ""))
                    or not isinstance(artifact.get("size"), int)
                    or artifact["size"] <= 0
                ):
                    raise ValidationError(f"{key}: malformed artifact receipt")
            if len(component.get("registry_urls", [])) != 2 or any(
                not re.fullmatch(
                    r"https://(?:github\.com/GBeurier/[A-Za-z0-9_.-]+/releases/tag/[A-Za-z0-9_.-]+|pypi\.org/project/[A-Za-z0-9_.-]+/[0-9A-Za-z.-]+/)",
                    registry_url,
                )
                for registry_url in component["registry_urls"]
            ):
                raise ValidationError(f"{key}: malformed registry receipt URL")
        elif component.get("publication") != "published":
            raise ValidationError(f"{key}: publication receipt is missing")
        for artifact in component.get("artifacts", []):
            if not re.fullmatch(r"[0-9a-f]{64}", artifact.get("sha256", "")):
                raise ValidationError(f"{key}: malformed artifact receipt")
        if not re.fullmatch(r"https://github\.com/GBeurier/[A-Za-z0-9_.-]+", component.get("repository_url", "")):
            raise ValidationError(f"{key}: unsafe candidate repository URL")
    if observed != CANDIDATE_COMPONENTS:
        raise ValidationError("native candidate identities diverge from the pinned Governance receipt")
    benchmarks = next(component for component in components if component.get("key") == "benchmarks")
    if benchmarks.get("qualification") != "final_functional_soak_passed_performance_budgets_separate":
        raise ValidationError("bounded V1 soak receipt diverges")

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
        performance.get("evidence_mode") != "v1_bounded_functional_soak_passed_sustained_budgets_deferred"
        or performance.get("contract") != "archive_v2_same_matrix_four_surfaces"
        or performance.get("budgets_frozen") is not False
        or performance.get("release_eligible") is not True
        or performance.get("representative_soak_required") is not False
        or performance.get("report_scope") != "python_3_cycles_and_studio_30_readiness_repetitions"
        or performance.get("duration_seconds") != 147.512
    ):
        raise ValidationError("bounded V1 soak receipt diverges")
    if candidate.get("work_item_states") != CANDIDATE_WORK_ITEM_STATES:
        raise ValidationError("selected work-item states are incomplete or overclaimed")

    functional = candidate.get("functional_non_crash")
    if functional != {
        "release_gate": True,
        "scope": "python_21_of_21_and_studio_90_of_90_checks",
        "status": "complete_functional_campaign_passed",
        "work_item": "SOAK-001",
    }:
        raise ValidationError("ROB-001 functional non-crash scope diverges")

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
    if not {"qualified_local", "qualified_bounded", "bounded_v1_functional_soak_passed"}.issubset(statuses):
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
        "Train produit GO — Python R1/R2/R3/R4, Studio, Web, Repository et Providers publiés",
        "native-candidate-staging.json",
        "Train R1/R2/R3/R4 distinct",
        "Capability matrix qualifiée",
        "Codes 0/10/20",
        "CUT-002",
        "Performance · preuve bornée non promotionnelle",
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


def validate_transition_copy(readme: str, index: str, release_page: str) -> None:
    """Keep human transition copy aligned with the candidate projection."""
    required = {
        "README.md": (
            "Python R1 0.13.0, R2, R3 and stable R4 1.0.0",
            "Repository 0.1.12 and Providers 0.2.11 are published",
            "Web 0.1.10 is deployed",
            "d7d62825e5aa5ab5554ec7d084fab29be66acd74",
            "d7fec320b6906c192bd7388f3137436ab8875e135f440ce1461c89379b537450",
        ),
        "index.html": (
            "Python R1 0.13.0, R2, R3 and stable R4 1.0.0</b>",
            "Repository 0.1.12</b>",
            "Providers 0.2.11</b>",
            "nirs4all-web 0.1.10</b> is live",
            "R4 1.0.0</b> and <b>Studio 0.11.0</b> are published",
        ),
        "release-status.html": (
            "Python R1/R2/R3/R4 et Studio publiés · GO",
            "python_r1_r2_r3_r4_and_studio_published",
            "R2/R3/R4 ont leurs reçus PyPI/GHCR",
        ),
    }
    documents = {
        "README.md": re.sub(r"\s+", " ", readme),
        "index.html": re.sub(r"\s+", " ", index),
        "release-status.html": re.sub(r"\s+", " ", release_page),
    }
    stale_markers = (
        "nirs4all-web 0.1.9",
        "Web 0.1.9",
        "R1 is still in progress",
        "R1 rollout is still in progress",
        "R1 product rollout remains in progress",
        "R1 reste en cours",
        "déploiement produit R1 reste en cours",
        "R1 in progress",
    )
    for name, text in documents.items():
        for marker in stale_markers:
            if marker in text:
                raise ValidationError(f"{name}: stale transition copy {marker!r}")
    for name, markers in required.items():
        for marker in markers:
            if marker not in documents[name]:
                raise ValidationError(f"{name}: transition copy missing {marker!r}")


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
        "['methods', 'providers', 'repository'].includes(component.key)",
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
        validate_transition_copy(
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "index.html").read_text(encoding="utf-8"),
            (ROOT / "release-status.html").read_text(encoding="utf-8"),
        )
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
