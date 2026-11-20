#!/usr/bin/env python3
"""Project the ecosystem release lock into the public static-site manifest.

The projection is intentionally conservative: a lock records selected source
versions and commits, but it does not prove that downloadable artifacts exist.
Publication is explicitly not assessed by this source lock, and artifacts are
not projected. This does not assert that the selected packages are unpublished.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


CURRENT_SCHEMA = "n4a.org-release-manifest/v2"
SOURCE_LOCK_SCHEMA = "n4a.aggregation-lock/v1"
SOURCE_TRAIN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SOURCE_STATUSES = {"candidate", "final"}
COMPONENT_REPOSITORIES = {
    "core": "nirs4all-core",
    "dag_ml": "dag-ml",
    "dag_ml_data": "dag-ml-data",
    "datasets": "nirs4all-datasets",
    "formats": "nirs4all-formats",
    "io": "nirs4all-io",
    "methods": "nirs4all-methods",
}
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
LOCK_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_KEYS = (
    "python",
    "rust_workspace",
    "rust",
    "python_nirs4all_methods",
)


class ProjectionError(ValueError):
    """Raised when release-lock evidence is incomplete or ambiguous."""


def source_release_train(identity: Any, status: Any) -> dict[str, Any]:
    """Describe the selected source cohort without assessing publication."""
    if not isinstance(identity, str) or not SOURCE_TRAIN_RE.fullmatch(identity):
        raise ProjectionError("missing or invalid source release_train identity")
    if not isinstance(status, str) or status not in SOURCE_STATUSES:
        raise ProjectionError("unsupported source release_train status")
    return {
        "id": identity,
        "source_status": status,
        "publication_assessment": "not_assessed_by_source_lock",
        "artifacts_projection": "not_projected",
        "message": (
            "Publication is not assessed by this source lock; "
            "artifacts are not projected."
        ),
    }


def _read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProjectionError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectionError(f"expected a JSON object in {path}")
    return value, raw


def _component_version(component_id: str, member: dict[str, Any]) -> str:
    versions = member.get("versions")
    if not isinstance(versions, dict):
        raise ProjectionError(f"{component_id}: missing versions object")

    candidates: list[str] = []
    for key in VERSION_KEYS:
        source = versions.get(key)
        if not isinstance(source, dict):
            continue
        value = source.get("value")
        if not isinstance(value, str) or not VERSION_RE.fullmatch(value):
            raise ProjectionError(f"{component_id}: invalid public scalar version")
        candidates.append(value)

    if not candidates:
        raise ProjectionError(
            f"{component_id}: no public scalar version in release lock"
        )
    if len(set(candidates)) != 1:
        raise ProjectionError(
            f"{component_id}: divergent public versions in release lock: "
            + ", ".join(sorted(set(candidates)))
        )
    return candidates[0]


def project_lock(lock: dict[str, Any], raw_lock: bytes) -> dict[str, Any]:
    """Return a deterministic, fail-closed public projection of *lock*."""

    if lock.get("schema_version") != SOURCE_LOCK_SCHEMA:
        raise ProjectionError("unsupported source-lock schema")
    if type(lock.get("aggregation_lock_version")) is not int or lock["aggregation_lock_version"] != 1:
        raise ProjectionError("unsupported aggregation_lock_version")
    train = source_release_train(lock.get("release_train"), lock.get("status"))
    manifest_digest = lock.get("manifest_digest")
    if not isinstance(manifest_digest, str) or not LOCK_DIGEST_RE.fullmatch(
        manifest_digest
    ):
        raise ProjectionError("missing or invalid manifest_digest")
    members = lock.get("members")
    if not isinstance(members, dict) or not members:
        raise ProjectionError("release lock contains no members")

    if set(members) != set(COMPONENT_REPOSITORIES):
        raise ProjectionError("release-lock member IDs must match the declared owner cohort")

    projected_components: list[dict[str, Any]] = []
    for component_id in sorted(members):
        value = members[component_id]
        if not isinstance(component_id, str) or not isinstance(value, dict):
            raise ProjectionError("invalid release-lock member")
        state = value.get("state")
        if not isinstance(state, dict):
            raise ProjectionError(f"{component_id}: missing repository state")
        if state.get("dirty") is not False:
            raise ProjectionError(f"{component_id}: dirty source cannot be staged")
        commit_sha = state.get("commit")
        if not isinstance(commit_sha, str) or not COMMIT_RE.fullmatch(commit_sha):
            raise ProjectionError(f"{component_id}: invalid commit SHA")
        repo = value.get("target_repo_url") or value.get("repo_url")
        name = value.get("target_repo_path") or value.get("repo_path")
        expected_name = COMPONENT_REPOSITORIES[component_id]
        if repo != f"GBeurier/{expected_name}" or name != expected_name:
            raise ProjectionError(f"{component_id}: unexpected public owner identity")

        projected_components.append(
            {
                "id": component_id,
                "name": name,
                "repository_url": f"https://github.com/{repo}",
                "version": _component_version(component_id, value),
                "commit_sha": commit_sha,
                "publication": {
                    "assessment": "not_assessed_by_source_lock",
                    "artifacts": [],
                },
            }
        )

    return {
        "schema_version": CURRENT_SCHEMA,
        "source_lock": {
            "aggregation_lock_version": 1,
            "manifest_digest": manifest_digest,
            "lock_sha256": "sha256:" + hashlib.sha256(raw_lock).hexdigest(),
            "repository_url": "https://github.com/GBeurier/nirs4all-ecosystem",
            "path": "docs/contracts/release/aggregation-lock.n4a.lock.json",
        },
        "release_train": train,
        "components": projected_components,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    lock, raw_lock = _read_json(args.lock)
    projected = project_lock(lock, raw_lock)
    args.output.write_text(
        json.dumps(projected, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
