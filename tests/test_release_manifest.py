from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from project_release_lock import (  # noqa: E402
    COMPONENT_REPOSITORIES, CURRENT_SCHEMA, ProjectionError, project_lock,
)
from validate_site import (  # noqa: E402
    ValidationError,
    validate_native_candidate,
    validate_release_manifest,
    validate_transition_copy,
)


def sample_lock() -> dict[str, object]:
    lock = {
        "schema_version": "n4a.aggregation-lock/v1",
        "aggregation_lock_version": 1,
        "release_train": "synthetic-source-cohort",
        "status": "candidate",
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
    for component_id, name in COMPONENT_REPOSITORIES.items():
        member = copy.deepcopy(lock["members"]["core"])
        member["repo_path"] = name
        member["repo_url"] = f"GBeurier/{name}"
        lock["members"][component_id] = member
    return lock


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
            component["publication"], {"assessment": "not_assessed_by_source_lock", "artifacts": []}
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

    def test_identity_and_source_status_come_from_lock_without_publication_claim(self) -> None:
        lock = sample_lock()
        lock["release_train"] = "another-source-cohort"
        lock["status"] = "final"
        projected = project_lock(lock, b"lock")
        self.assertEqual(projected["schema_version"], CURRENT_SCHEMA)
        self.assertEqual(projected["release_train"]["id"], "another-source-cohort")
        self.assertEqual(projected["release_train"]["source_status"], "final")
        self.assertNotIn("published", projected["release_train"])
        self.assertEqual(projected["release_train"]["artifacts_projection"], "not_projected")
        self.assertTrue(all(c["publication"]["assessment"] == "not_assessed_by_source_lock" for c in projected["components"]))

    def test_unknown_source_schemas_ids_status_and_owner_identity_are_rejected(self) -> None:
        for field, value in [("schema_version", "unknown"), ("aggregation_lock_version", 2), ("release_train", "../private"), ("status", "published")]:
            with self.subTest(field=field):
                lock = sample_lock()
                lock[field] = value
                with self.assertRaises(ProjectionError):
                    project_lock(lock, b"lock")
        for mutation in ("unknown", "missing", "repository"):
            with self.subTest(mutation=mutation):
                lock = sample_lock()
                if mutation == "unknown":
                    lock["members"]["unknown"] = copy.deepcopy(lock["members"]["core"])
                elif mutation == "missing":
                    del lock["members"]["core"]
                else:
                    lock["members"]["core"]["repo_url"] = "someone/unrelated"
                with self.assertRaises(ProjectionError):
                    project_lock(lock, b"lock")

    def test_source_labels_cannot_be_promoted_to_artifact_evidence(self) -> None:
        lock = sample_lock()
        lock["members"]["core"]["publication"] = {"state": "published", "artifacts": [{"url": "https://example.org/unproven"}]}
        projected = project_lock(lock, b"lock")
        self.assertEqual(projected["components"][0]["publication"], {"assessment": "not_assessed_by_source_lock", "artifacts": []})


class CurrentManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = project_lock(sample_lock(), b"synthetic lock")

    def test_valid_current_manifest_is_source_only(self) -> None:
        validate_release_manifest(self.manifest)
        self.assertNotIn("published", self.manifest["release_train"])

    def test_unknown_schema_id_duplicate_missing_and_repo_are_rejected(self) -> None:
        for mutation in ("schema", "id", "duplicate", "missing", "repository"):
            with self.subTest(mutation=mutation):
                invalid = copy.deepcopy(self.manifest)
                if mutation == "schema":
                    invalid["schema_version"] = "unknown"
                elif mutation == "id":
                    invalid["components"][0]["id"] = "unknown"
                elif mutation == "duplicate":
                    invalid["components"][1] = copy.deepcopy(invalid["components"][0])
                elif mutation == "missing":
                    invalid["components"].pop()
                else:
                    invalid["components"][0]["repository_url"] = "https://github.com/someone/unrelated"
                with self.assertRaises(ValidationError):
                    validate_release_manifest(invalid)

    def test_unassessed_publication_and_no_artifact_projection_are_required(self) -> None:
        for publication in ({"assessment": "published", "artifacts": []}, {"assessment": "unpublished", "artifacts": []}, {"assessment": "not_assessed_by_source_lock", "artifacts": [{"name": "unproven", "url": "https://example.org/unproven", "sha256": "sha256:" + "c" * 64}]}, {"state": "pending", "artifacts": []}):
            with self.subTest(publication=publication):
                invalid = copy.deepcopy(self.manifest)
                invalid["components"][0]["publication"] = publication
                with self.assertRaises(ValidationError):
                    validate_release_manifest(invalid)
        invalid = copy.deepcopy(self.manifest)
        invalid["release_train"]["published"] = False
        with self.assertRaises(ValidationError):
            validate_release_manifest(invalid)

    def test_source_lock_version_requires_an_integer_one(self) -> None:
        for version in (True, 1.0, 2):
            with self.subTest(version=version):
                invalid = copy.deepcopy(self.manifest)
                invalid["source_lock"]["aggregation_lock_version"] = version
                with self.assertRaisesRegex(ValidationError, "version must be 1"):
                    validate_release_manifest(invalid)

    def test_invalid_train_or_unknown_field_is_refused(self) -> None:
        for key, value in [("source_status", "published"), ("id", "../private"), ("artifacts_projection", "available"), ("extra", True)]:
            with self.subTest(key=key):
                invalid = copy.deepcopy(self.manifest)
                invalid["release_train"][key] = value
                with self.assertRaises(ValidationError):
                    validate_release_manifest(invalid)


class PublicManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(
            (ROOT / "release-manifest-r2-history.json").read_text(encoding="utf-8")
        )

    def test_historical_manifest_is_valid(self) -> None:
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

    def test_committed_release_projection_is_exact_and_published(self) -> None:
        validate_native_candidate(self.candidate)

    def test_release_projection_refuses_bad_artifact_or_state_downgrade(self) -> None:
        invalid = copy.deepcopy(self.candidate)
        invalid["components"][0]["artifacts"] = [{"sha256": "bad"}]
        with self.assertRaisesRegex(ValidationError, "malformed artifact"):
            validate_native_candidate(invalid)

        invalid = copy.deepcopy(self.candidate)
        invalid["release"]["status"] = "no_go"
        with self.assertRaisesRegex(ValidationError, "GO and published"):
            validate_native_candidate(invalid)

    def test_release_train_must_remain_distinct_and_published(self) -> None:
        invalid = copy.deepcopy(self.candidate)
        invalid["release_train"]["milestones"]["r2"]["studio_commit"] = invalid[
            "release_train"
        ]["milestones"]["r3"]["studio_commit"]
        with self.assertRaisesRegex(ValidationError, "r2 identities diverge"):
            validate_native_candidate(invalid)

        invalid = copy.deepcopy(self.candidate)
        invalid["release_train"]["publication"] = "published"
        with self.assertRaisesRegex(ValidationError, "all published receipts"):
            validate_native_candidate(invalid)

    def test_bounded_v1_soak_receipt_cannot_be_overclaimed(self) -> None:
        invalid = copy.deepcopy(self.candidate)
        invalid["performance"]["evidence_mode"] = "local_real_record_only"
        with self.assertRaisesRegex(ValidationError, "bounded V1 soak"):
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
                self.index + "\n<p>nirs4all-web 0.1.9</p>\n",
                self.release_page,
            )
        with self.assertRaisesRegex(ValidationError, "stale transition copy"):
            validate_transition_copy(
                self.readme + "\nR1 is still in progress.\n",
                self.index,
                self.release_page,
            )
        with self.assertRaisesRegex(ValidationError, "stale transition copy"):
            validate_transition_copy(
                self.readme,
                self.index + "\n<p>Download Studio 0.11.11</p>\n",
                self.release_page,
            )

    def test_current_source_hook_and_history_separation_are_required(self) -> None:
        with self.assertRaisesRegex(ValidationError, "transition copy missing"):
            validate_transition_copy(self.readme, self.index.replace('data-ver="gh:nirs4all-core"', 'data-ver="unknown"'), self.release_page)
        with self.assertRaisesRegex(ValidationError, "transition copy missing"):
            validate_transition_copy(self.readme, self.index, self.release_page.replace('id="current-source-cohort"', 'id="unknown"'))


if __name__ == "__main__":
    unittest.main()
