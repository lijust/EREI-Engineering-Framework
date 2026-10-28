"""Bounded offline Core13 capability preview using existing project files and policy.

No live capability dispatch and no project writes. The model can propose an
action but cannot provide activation files, project pins, or adoption records.
This is local source-consistency checking, NOT independent authentication.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

from tools import capability_activation as activation
from tools import learning_proposal_runtime as pilot


def _denied(reason: str) -> dict:
    return {
        "kind": "EREI_PROJECT_ACTIVATION_PREVIEW_V1",
        "status": "DENIED",
        "reason_code": reason,
        "executed": False,
        "independently_verified": False,
        "model_original_score_changed": False,
        "stable_ready": False,
        "source_authority": "LOCAL_FILES_AND_GIT_CHECKOUT_NOT_INDEPENDENTLY_ATTESTED",
    }


def _digest(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def evaluate_activation_from_project(
    proposal: Any, project_root: Path | str, capability: str, *, now: datetime,
) -> dict:
    """Preview action authorization against existing activation resolver.

    Caller chooses the project directory, capability and aware clock.
    The project manifest, Framework registry, adoption record and loaded
    Framework revision are loaded from their existing sources, not supplied
    in the model proposal. Caller must not use this as an execution token.
    """
    if (not isinstance(project_root, (Path, str)) or not str(project_root).strip()
            or type(capability) is not str or not capability.strip()):
        return _denied("ACTIVATION_TARGET_INVALID")
    if type(now) is not datetime or now.tzinfo is None or now.utcoffset() is None:
        return _denied("ACTIVATION_CLOCK_UNVERIFIED")

    try:
        project = Path(project_root).resolve(strict=True)
        if not project.is_dir():
            return _denied("ACTIVATION_TARGET_INVALID")
        activation.assert_clean_framework_checkout()

        manifest_path = project / activation.MANIFEST_PATH
        registry_path = activation.REGISTRY_PATH
        adoption_path = project / activation.ADOPTION_PATH
        files = {"manifest": manifest_path, "registry": registry_path,
                 "adoption": adoption_path}
        before = {name: _digest(path) for name, path in files.items()}

        manifest = activation._read_json(manifest_path, "project framework manifest")
        registry = activation._read_json(registry_path, "Framework capability registry")
        adoption = (activation._read_json(adoption_path, "candidate capability adoption")
                    if adoption_path.exists() else None)
        framework = activation._validate_manifest(manifest)

        loaded_ref = activation.detect_loaded_framework_ref()
        resolved_ref = (activation.resolve_project_tag_ref(framework["ref"])
                        if framework["ref_type"] == "tag" else None)
        context = {
            "domain": "capability_activation", "capability": capability,
            "manifest": manifest, "registry": registry,
            "adoption_document": adoption,
            "loaded_framework_ref": loaded_ref,
            "resolved_project_ref": resolved_ref,
            "now": now,
        }
        # Source-derived resolution seeds the simulation's initial status.
        # This does not represent a project capability execution history.
        resolution = activation.resolve_activation(
            manifest, registry, capability, adoption_document=adoption,
            loaded_framework_ref=loaded_ref, resolved_project_ref=resolved_ref,
            now=now,
        )
        current = resolution["status"]
        initial_status = (
            "STABLE" if current == "ACTIVE_STABLE" else
            "ACTIVE_CANDIDATE" if current == "ACTIVE_CANDIDATE" else
            "DORMANT" if current == "DORMANT_CANDIDATE" else "BLOCKED"
        )
        result = pilot.evaluate_proposal(
            proposal, {"capability_status": initial_status, "executions": []},
            context,
        )

        # Detect ordinary local source/checkout changes during the preview.
        # No atomic snapshot, remote provenance, or post-return lock is claimed.
        if (before != {name: _digest(path) for name, path in files.items()}
                or activation.detect_loaded_framework_ref() != loaded_ref):
            return _denied("ACTIVATION_SOURCE_CHANGED_DURING_PREVIEW")
        activation.assert_clean_framework_checkout()

        return {
            **result,
            "kind": "EREI_PROJECT_ACTIVATION_PREVIEW_V1",
            "source_authority": "LOCAL_FILES_AND_GIT_CHECKOUT_NOT_INDEPENDENTLY_ATTESTED",
            "source_binding": {
                "framework_checkout_sha": loaded_ref,
                "manifest_sha256": before["manifest"],
                "registry_sha256": before["registry"],
                "adoption_sha256": before["adoption"],
                "resolver_status": current,
                "capability": capability,
                "simulation_seed": "RESOLVER_STATUS_WITH_EMPTY_EXECUTION_HISTORY",
            },
        }
    except (activation.ActivationError, OSError, TypeError, ValueError,
            KeyError, AttributeError, UnicodeError):
        return _denied("ACTIVATION_SOURCE_UNVERIFIED")
