#!/usr/bin/env python3
"""Project the ecosystem release lock into the public static-site manifest.

The projection is intentionally conservative: a lock records selected source
versions and commits, but it does not prove that downloadable artifacts exist.
Consequently every projected component remains pending until a later,
artifact-aware release-lock format can carry verifiable publication evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


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
        if isinstance(value, str) and value:
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

    if lock.get("aggregation_lock_version") != 1:
        raise ProjectionError("unsupported aggregation_lock_version")
    manifest_digest = lock.get("manifest_digest")
    if not isinstance(manifest_digest, str) or not LOCK_DIGEST_RE.fullmatch(
        manifest_digest
    ):
        raise ProjectionError("missing or invalid manifest_digest")
    members = lock.get("members")
    if not isinstance(members, dict) or not members:
        raise ProjectionError("release lock contains no members")

    projected_components: list[dict[str, Any]] = []
    for component_id, value in members.items():
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
        if not isinstance(repo, str) or not re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo
        ):
            raise ProjectionError(f"{component_id}: invalid public repository")

        projected_components.append(
            {
                "id": component_id,
                "name": value.get("target_repo_path")
                or value.get("repo_path")
                or component_id,
                "repository_url": f"https://github.com/{repo}",
                "version": _component_version(component_id, value),
                "commit_sha": commit_sha,
                "publication": {
                    "state": "pending",
                    "artifacts": [],
                },
            }
        )

    return {
        "schema_version": "n4a.org-release-manifest/v1",
        "source_lock": {
            "aggregation_lock_version": 1,
            "manifest_digest": manifest_digest,
            "lock_sha256": "sha256:" + hashlib.sha256(raw_lock).hexdigest(),
            "repository_url": "https://github.com/GBeurier/nirs4all-ecosystem",
            "path": "docs/contracts/release/aggregation-lock.n4a.lock.json",
        },
        "release_train": {
            "milestone": "R2",
            "state": "in_progress",
            "published": False,
            "message": "Publication en cours — le jalon R2 reste incomplet.",
        },
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
