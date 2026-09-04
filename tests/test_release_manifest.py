from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from project_release_lock import ProjectionError, project_lock  # noqa: E402
from validate_site import (  # noqa: E402
    ValidationError,
    validate_native_candidate,
    validate_release_manifest,
    validate_transition_copy,
)


def sample_lock() -> dict[str, object]:
    return {
        "aggregation_lock_version": 1,
        "manifest_digest": "sha256:" + "a" * 64,
        "members": {
            "core": {
                "repo_path": "nirs4all-core",
                "repo_url": "GBeurier/nirs4all-core",
                "selected_workspace_path": "/private/worktree/that/must/not/leak",
                "state": {
                    "branch": "candidate/local-only",
                    "commit": "b" * 40,
                    "dirty": False,
                    "exact_tag": None,
                },
                "versions": {
                    "python": {"value": "1.2.3", "source": "/private/pyproject.toml"},
                    "rust": {"value": "1.2.3", "source": "Cargo.toml"},
                },
            }
        },
    }


class ProjectReleaseLockTests(unittest.TestCase):
    def test_projection_is_public_deterministic_and_fail_closed(self) -> None:
        lock = sample_lock()
        first = project_lock(lock, b"same bytes")
        second = project_lock(copy.deepcopy(lock), b"same bytes")
        self.assertEqual(first, second)
        component = first["components"][0]
        self.assertEqual(component["version"], "1.2.3")
        self.assertEqual(component["commit_sha"], "b" * 40)
        self.assertEqual(
            component["publication"], {"state": "pending", "artifacts": []}
        )
        serialized = json.dumps(first)
        self.assertNotIn("selected_workspace_path", serialized)
        self.assertNotIn("/private/", serialized)
        self.assertNotIn("candidate/local-only", serialized)

    def test_dirty_member_is_rejected(self) -> None:
        lock = sample_lock()
        lock["members"]["core"]["state"]["dirty"] = True  # type: ignore[index]
        with self.assertRaisesRegex(ProjectionError, "dirty source"):
            project_lock(lock, b"lock")

    def test_divergent_public_versions_are_rejected(self) -> None:
        lock = sample_lock()
        lock["members"]["core"]["versions"]["rust"]["value"] = "1.2.4"  # type: ignore[index]
        with self.assertRaisesRegex(ProjectionError, "divergent public versions"):
            project_lock(lock, b"lock")


class PublicManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(
            (ROOT / "release-manifest.json").read_text(encoding="utf-8")
        )

    def test_committed_manifest_is_valid(self) -> None:
        validate_release_manifest(self.manifest)

    def test_pending_component_cannot_expose_download(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        invalid["components"][0]["publication"]["artifacts"] = [
            {
                "name": "not-proven.zip",
                "url": "https://example.org/not-proven.zip",
                "sha256": "sha256:" + "c" * 64,
            }
        ]
        with self.assertRaisesRegex(ValidationError, "pending component"):
            validate_release_manifest(invalid)

    def test_published_component_requires_artifact(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        invalid["components"][0]["publication"]["state"] = "published"
        with self.assertRaisesRegex(ValidationError, "requires artifacts"):
            validate_release_manifest(invalid)

    def test_local_path_leak_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        invalid["source_lock"]["path"] = "/dev/shm/private-lock.json"
        with self.assertRaises(ValidationError):
            validate_release_manifest(invalid)

    def test_unexpected_field_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.manifest)
        invalid["components"][0]["selected_workspace_path"] = "/tmp/worktree"
        with self.assertRaisesRegex(ValidationError, "expected keys"):
            validate_release_manifest(invalid)


class NativeCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.candidate = json.loads(
            (ROOT / "native-candidate-staging.json").read_text(encoding="utf-8")
        )

    def test_committed_candidate_is_exact_and_unpublished(self) -> None:
        validate_native_candidate(self.candidate)

    def test_candidate_cannot_gain_artifact_or_go_status(self) -> None:
        invalid = copy.deepcopy(self.candidate)
        invalid["components"][0]["artifacts"] = [
            {"url": "https://example.invalid/fake.zip"}
        ]
        with self.assertRaisesRegex(ValidationError, "exposes publication"):
            validate_native_candidate(invalid)

        invalid = copy.deepcopy(self.candidate)
        invalid["release"]["status"] = "go"
        with self.assertRaisesRegex(ValidationError, "NO-GO"):
            validate_native_candidate(invalid)

    def test_candidate_train_must_remain_distinct_with_only_r1_published(self) -> None:
        invalid = copy.deepcopy(self.candidate)
        invalid["release_train"]["milestones"]["r2"]["studio_commit"] = invalid[
            "release_train"
        ]["milestones"]["r3"]["studio_commit"]
        with self.assertRaisesRegex(ValidationError, "r2 identities diverge"):
            validate_native_candidate(invalid)

        invalid = copy.deepcopy(self.candidate)
        invalid["release_train"]["publication"] = "published"
        with self.assertRaisesRegex(ValidationError, "published R1 receipt"):
            validate_native_candidate(invalid)

    def test_bounded_bench_replay_cannot_become_release_evidence(self) -> None:
        invalid = copy.deepcopy(self.candidate)
        invalid["performance"]["evidence_mode"] = "local_real_record_only"
        with self.assertRaisesRegex(ValidationError, "bounded Bench replay"):
            validate_native_candidate(invalid)


class TransitionCopyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.release_page = (ROOT / "release-status.html").read_text(
            encoding="utf-8"
        )

    def test_committed_transition_copy_matches_candidate(self) -> None:
        validate_transition_copy(self.readme, self.index, self.release_page)

    def test_stale_web_or_r1_copy_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValidationError, "stale transition copy"):
            validate_transition_copy(
                self.readme,
                self.index.replace("nirs4all-web 0.1.10", "nirs4all-web 0.1.9"),
                self.release_page,
            )
        with self.assertRaisesRegex(ValidationError, "stale transition copy"):
            validate_transition_copy(
                self.readme + "\nR1 is still in progress.\n",
                self.index,
                self.release_page,
            )


if __name__ == "__main__":
    unittest.main()
