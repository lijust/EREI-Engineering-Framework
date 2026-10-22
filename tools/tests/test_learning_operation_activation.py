"""Project entrypoint regressions using the real activation resolver.

Only the loaded Git identity/cleanliness boundary is mocked: these tests do not
claim to exercise a protected runtime, signing service, or AI workflow engine.
All project manifests, adoptions, ledgers and outputs are temporary fixtures.
"""
from __future__ import annotations

import argparse
import copy
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from tools import capability_activation as activation
from tools import learning_development_output as ldo
from tools import learning_effectiveness as effectiveness
from tools import learning_pattern_analysis as pattern
from tools import learning_review_debt_gate as debt


ROOT = Path(__file__).resolve().parents[2]
PIN = "a" * 40
CAPABILITIES = (
    "learning_pattern_analysis",
    "learning_to_development",
    "learning_review_debt_guard",
    "framework_effectiveness_measurement",
)


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def timestamp(value):
    return value.isoformat().replace("+00:00", "Z")


class LearningOperationActivationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.target = Path(self.tmp.name)
        (self.target / ".erei").mkdir()
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.project = {
            "schema_version": 1,
            "framework": {
                "repository": "lijust/EREI-Engineering-Framework",
                "baseline": "candidate-trial",
                "ref_type": "commit", "ref": PIN,
            },
            "project": {}, "overlays": [], "runtime_adapters": [],
        }
        write_json(self.target / activation.MANIFEST_PATH, self.project)
        self.registry = json.loads((ROOT / "CAPABILITIES.json").read_text(encoding="utf-8"))
        self.registry_path = self.target / "registry.json"
        write_json(self.registry_path, self.registry)
        self.stack = self.enterContext(ExitStack())
        self.stack.enter_context(mock.patch.object(activation, "REGISTRY_PATH", self.registry_path))
        self.clean = self.stack.enter_context(mock.patch.object(activation, "assert_clean_framework_checkout"))
        self.loaded = self.stack.enter_context(mock.patch.object(activation, "detect_loaded_framework_ref", return_value=PIN))
        self.state = pattern.authoritative_task_learning.derive_state([], [], now=self.now)
        self.state_path = self.target / "state.json"
        write_json(self.state_path, self.state)

    def adopt(self, capabilities=CAPABILITIES, *, expired=False, wrong_ref=False, wrong_version=False):
        items = []
        for number, capability in enumerate(capabilities):
            items.append({
                "adoption_id": f"CAD-20261015T200000Z-{number:08X}",
                "capability": capability,
                "version": "wrong-version" if wrong_version else self.registry["development_line"]["capabilities"][capability]["version"],
                "approved_at": timestamp(self.now - timedelta(days=1)),
                "expires_at": timestamp(self.now - timedelta(seconds=1) if expired else self.now + timedelta(days=7)),
                "approved_by_role": "chief-engineer", "risk": "L2",
                "purpose": "Isolated bounded activation regression fixture.",
                "evidence": ["test:activation-boundary"],
            })
        value = {"schema_version": 1, "framework_ref": "b" * 40 if wrong_ref else PIN, "adoptions": items}
        write_json(self.target / activation.ADOPTION_PATH, value)

    def cli(self, main, arguments):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = main(arguments)
        return result, stdout.getvalue()

    def assert_denied_cli_set(self, expected):
        """Gate must run before missing payloads or analyzer output writes."""
        output = self.target / "analysis.json"
        markdown = self.target / "analysis.md"
        missing = str(self.target / "not-readable.json")
        project = ["--target", str(self.target)]
        invocations = (
            (pattern.main, project + ["--json-output", str(output), "--markdown-output", str(markdown)]),
            (ldo.main, project + ["--input", missing]),
            (effectiveness.main, project + ["--before", missing, "--after", missing]),
            (debt.main, project + ["--state", str(self.state_path), "--defer", missing]),
        )
        with mock.patch.object(pattern.authoritative_task_learning, "authoritative_snapshot") as snapshot, \
             mock.patch.object(ldo, "validate") as validate, \
             mock.patch.object(effectiveness, "_load") as load, \
             mock.patch.object(debt, "validate_defer") as defer:
            for main, args in invocations:
                with self.subTest(tool=main.__module__):
                    code, stdout = self.cli(main, args)
                    self.assertEqual(code, 3, stdout)
                    self.assertEqual(json.loads(stdout)["status"], expected)
            snapshot.assert_not_called()
            validate.assert_not_called()
            load.assert_not_called()
            defer.assert_not_called()
        self.assertFalse(output.exists())
        self.assertFalse(markdown.exists())

    def test_direct_clis_are_dormant_without_adoption(self):
        self.assert_denied_cli_set("DORMANT_CANDIDATE")

    def test_direct_clis_reject_expired_adoption(self):
        self.adopt(expired=True)
        self.assert_denied_cli_set("BLOCK_EXPIRED_CANDIDATE_ADOPTION")

    def test_direct_clis_reject_wrong_adoption_ref(self):
        self.adopt(wrong_ref=True)
        self.assert_denied_cli_set("BLOCK_FRAMEWORK_REF_MISMATCH")

    def test_direct_clis_reject_wrong_capability_version(self):
        self.adopt(wrong_version=True)
        self.assert_denied_cli_set("BLOCK_CANDIDATE_VERSION_MISMATCH")

    def test_direct_clis_reject_loaded_framework_mismatch(self):
        self.adopt()
        self.loaded.return_value = "b" * 40
        self.assert_denied_cli_set("BLOCK_FRAMEWORK_REF_MISMATCH")

    def test_direct_clis_reject_unresolved_framework(self):
        self.adopt()
        self.loaded.return_value = None
        self.assert_denied_cli_set("BLOCK_FRAMEWORK_CHECKOUT_UNRESOLVED")

    def test_direct_clis_reject_moving_branch_pin(self):
        self.project["framework"].update(ref_type="branch", ref="candidate-branch")
        write_json(self.target / activation.MANIFEST_PATH, self.project)
        self.assert_denied_cli_set("BLOCK_NON_COMMIT_PROJECT_PIN")

    def test_indirect_project_calls_require_their_own_adoption(self):
        self.adopt(["learning_to_development"])
        self.assertEqual(activation.require_active(self.target, "learning_to_development")["status"], "ACTIVE_CANDIDATE")
        calls = (
            lambda: pattern.analyze_target(self.target),
            lambda: effectiveness.compare_target(self.target, self.target / "missing", self.target / "missing"),
            lambda: debt.evaluate_target(self.target, self.state, defer_path=self.target / "missing"),
        )
        for call in calls:
            with self.assertRaises(activation.InactiveCapabilityError) as raised:
                call()
            self.assertEqual(raised.exception.result["status"], "DORMANT_CANDIDATE")

    def test_expired_parent_cannot_dispatch_even_with_active_subordinate(self):
        self.adopt()
        path = self.target / activation.ADOPTION_PATH
        document = json.loads(path.read_text(encoding="utf-8"))
        next(item for item in document["adoptions"] if item["capability"] == "learning_to_development")["expires_at"] = timestamp(self.now - timedelta(seconds=1))
        write_json(path, document)
        self.assertEqual(activation.require_active(self.target, "learning_pattern_analysis")["status"], "ACTIVE_CANDIDATE")
        with self.assertRaises(activation.InactiveCapabilityError) as raised:
            activation.require_active(self.target, "learning_to_development")
        self.assertEqual(raised.exception.result["status"], "BLOCK_EXPIRED_CANDIDATE_ADOPTION")

    def test_stable_capability_remains_callable_without_candidate_adoption(self):
        self.registry["development_line"]["capabilities"]["learning_review_debt_guard"]["status"] = "stable"
        write_json(self.registry_path, self.registry)
        self.assertEqual(debt.evaluate_target(self.target, self.state)["status"], "PASS_NO_IMMEDIATE_REVIEW")

    def test_core_critical_stop_precedes_adoption_or_defer(self):
        critical = copy.deepcopy(self.state)
        critical["metrics_since_last_review"]["security_or_data_critical_events"] = 1
        # Even a stale healthy trigger cannot hide a validated critical metric.
        critical["trigger"] = {"level": "LEARNING_HEALTHY", "reasons": []}
        write_json(self.state_path, critical)
        self.clean.side_effect = activation.ActivationError("checkout unavailable")
        with mock.patch.object(debt, "validate_defer") as defer:
            result = debt.evaluate_target(self.target, critical, defer_path=self.target / "missing")
            code, stdout = self.cli(debt.main, ["--target", str(self.target), "--state", str(self.state_path), "--defer", str(self.target / "missing")])
            self.assertEqual(result["status"], "BLOCK_CRITICAL_SECURITY_OR_DATA_REVIEW")
            self.assertEqual(json.loads(stdout)["status"], result["status"])
            self.assertEqual(code, 3)
            self.clean.assert_not_called()
            defer.assert_not_called()

    def test_invalid_core_state_fails_closed_before_optional_policy(self):
        with self.assertRaises(debt.ReviewDebtError):
            debt.evaluate_target(self.target, {})
        self.clean.assert_not_called()

    def test_active_candidate_rejects_stale_healthy_state_against_real_escape(self):
        self.adopt(["learning_review_debt_guard"])
        self.capture_event(verification_escape=True)
        events_path = self.target / ".erei/learning/TASK_EVENTS.jsonl"
        before = events_path.read_bytes()
        # An old LEARNING_HEALTHY projection cannot conceal a newer event.
        with self.assertRaisesRegex(debt.ReviewDebtError, "does not match authoritative ledgers"):
            debt.evaluate_target(self.target, self.state)
        code, output = self.cli(debt.main, ["--target", str(self.target), "--state", str(self.state_path)])
        self.assertEqual(code, 2)
        self.assertIn("does not match authoritative ledgers", output)
        self.assertEqual(events_path.read_bytes(), before)

    def test_active_candidate_rejects_invalid_authority_without_defer_read(self):
        self.adopt(["learning_review_debt_guard"])
        learning = self.target / ".erei/learning"
        learning.mkdir(parents=True, exist_ok=True)
        (learning / "TASK_EVENTS.jsonl").write_text("invalid-json\\n", encoding="utf-8")
        bad_defer = self.target / "missing_defer.json"
        with self.assertRaisesRegex(debt.ReviewDebtError, "cannot verify authoritative learning state"):
            debt.evaluate_target(self.target, self.state, defer_path=bad_defer)
        self.assertFalse(bad_defer.exists())

    def test_active_debt_policy_still_blocks_escape_and_accepts_bounded_defer(self):
        self.adopt(["learning_review_debt_guard"])
        self.capture_event(verification_escape=True)
        state = pattern.authoritative_task_learning.authoritative_snapshot(self.target)["state"]
        self.assertEqual(debt.evaluate_target(self.target, state)["status"], "BLOCK_IMMEDIATE_REVIEW_DEBT")
        record = {
            "schema_version": 1, "defer_id": "ELD-20261015T000000Z-ABCDEF12",
            "epoch_id": state["epoch_id"],
            "recorded_at": timestamp(self.now - timedelta(hours=1)),
            "expires_at": timestamp(self.now + timedelta(hours=1)),
            "baseline_material_tasks": 1, "max_additional_material_tasks": 1,
            "reason": "Isolated bounded defer regression fixture.",
            "reviewed_by_role": "chief-engineer", "evidence": ["test:defer"],
        }
        record["fingerprint"] = debt.defer_fingerprint(record)
        path = self.target / "defer.json"
        write_json(path, record)
        self.assertEqual(debt.evaluate_target(self.target, state, defer_path=path, now=self.now)["status"], "PASS_BOUNDED_REVIEW_DEFER")

    def capture_event(self, *, verification_escape=False):
        args = argparse.Namespace(
            task_id=None, occurrence_id=None, task_group="activation-regression",
            project_repository="example/repo", project_name="Fixture", framework_ref=PIN,
            workflow="feature-development", risk="L2", terminal_state="COMPLETE_VERIFIED",
            outcome_class="verified_success", material=True, rework_cycles=0,
            verification_failures=0, verification_escape=verification_escape, framework_feedback_created=False,
            manual_workaround=False, context_gap=False, unexpected_scope_growth=False,
            security_or_data_critical_event=False, duration_class="medium", failure_stage="none",
            failure_subject=None, feedback_id=[], feedback_fingerprint=[], tag=[],
        )
        event = pattern.authoritative_task_learning.build_event(args)
        pattern.authoritative_task_learning.capture(self.target, event)

    def output_fixture(self):
        return {
            "schema_version": 1, "output_id": "LDO-20261015T180000Z-ABCDEF12",
            "created_at": "2026-10-15T18:00:00Z",
            "source": {"project_repository": "example/repo", "epoch_id": "EPOCH-001"},
            "pattern": {"pattern_id": "LP-EXAMPLE-001", "pattern_class": "verification_escape", "signal_summary": "A prior proof was contradicted."},
            "interpretation": "A project-local proof needs further evidence.",
            "classification": "NEEDS_MORE_EVIDENCE", "development_route": "evidence_collection",
            "evidence": ["test:fixture"], "expected_effect": "Collect comparable verification evidence.",
            "success_metrics": [{"metric": "verification_escape_task_rate", "direction": "decrease"}],
            "promotion_boundary": "stable_review_required",
        }

    def test_active_direct_clis_perform_real_local_work(self):
        self.adopt()
        self.capture_event()
        report_path = self.target / "analysis.json"
        code, stdout = self.cli(pattern.main, ["--target", str(self.target), "--json-output", str(report_path)])
        self.assertEqual(code, 0, stdout)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["current_epoch"]["material_tasks"], 1)
        self.assertEqual(pattern.analyze_target(self.target), report)
        code, stdout = self.cli(effectiveness.main, ["--target", str(self.target), "--before", str(report_path), "--after", str(report_path)])
        self.assertEqual(code, 0, stdout)
        self.assertEqual(json.loads(stdout)["causation"], "NOT_ESTABLISHED")
        output_path = self.target / "output.json"
        write_json(output_path, self.output_fixture())
        code, stdout = self.cli(ldo.main, ["--target", str(self.target), "--input", str(output_path)])
        self.assertEqual((code, json.loads(stdout)["status"]), (0, "VALID"))
        write_json(self.state_path, pattern.authoritative_task_learning.authoritative_snapshot(self.target)["state"])
        code, stdout = self.cli(debt.main, ["--target", str(self.target), "--state", str(self.state_path)])
        self.assertEqual((code, json.loads(stdout)["status"]), (0, "PASS_NO_IMMEDIATE_REVIEW"))

    def test_pure_artifact_validation_and_calculations_do_not_activate_workflows(self):
        self.clean.side_effect = activation.ActivationError("no runtime checkout")
        path = self.target / "output.json"
        write_json(path, self.output_fixture())
        before = path.read_bytes()
        code, stdout = self.cli(ldo.main, ["--input", str(path)])
        self.assertEqual((code, json.loads(stdout)["status"]), (0, "VALID"))
        self.assertEqual(path.read_bytes(), before)
        report = pattern.analyze([], [], self.state)
        self.assertEqual(effectiveness.compare(report, report)["causation"], "NOT_ESTABLISHED")
        self.assertEqual(debt.evaluate(self.state, None, self.now)["status"], "PASS_NO_IMMEDIATE_REVIEW")
        self.clean.assert_not_called()

    def test_compiled_python_cache_does_not_dirty_repo_but_source_does(self):
        # A Python import normally creates __pycache__, which must not make
        # every subsequent governed CLI fail its clean-checkout boundary.
        # Ignore interpreter artifacts, NOT arbitrary untracked source files.
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
            (repo / ".gitignore").write_bytes((ROOT / ".gitignore").read_bytes())
            subprocess.run(["git", "add", ".gitignore"], cwd=repo, check=True)
            cache = repo / "tools/__pycache__"
            cache.mkdir(parents=True)
            (cache / "capability_activation.cpython-312.pyc").write_bytes(b"compiled")
            (repo / "tools/activation_probe.pyc").write_bytes(b"compiled")
            status = subprocess.run(
                ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                cwd=repo, capture_output=True, text=True, check=True,
            )
            self.assertEqual(status.stdout.strip(), "A  .gitignore")
            (repo / "tools/unsafe_untracked_source.py").write_text(
                "print('probe')\\n", encoding="utf-8"
            )
            changed = subprocess.run(
                ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                cwd=repo, capture_output=True, text=True, check=True,
            )
            self.assertIn("unsafe_untracked_source.py", changed.stdout)

    def test_dirty_checkout_cannot_dispatch(self):
        self.adopt()
        self.clean.side_effect = activation.ActivationError("dirty Framework checkout")
        with self.assertRaisesRegex(activation.ActivationError, "dirty"):
            pattern.analyze_target(self.target)


if __name__ == "__main__":
    unittest.main()
