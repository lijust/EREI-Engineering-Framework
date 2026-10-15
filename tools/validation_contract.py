#!/usr/bin/env python3
"""Shared strict validation primitives for EREI machine-readable contracts.

The Framework deliberately keeps this module dependency-free. JSON Schema remains the
published contract; these helpers implement the executable subset used by Framework
tooling and are parity-tested against the published schemas.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Iterable


RFC3339_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})$"
)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
TASK_ID_RE = re.compile(r"^ETASK-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
OCCURRENCE_ID_RE = re.compile(r"^EOCC-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
REVIEW_ID_RE = re.compile(r"^ELR-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
FEEDBACK_ID_RE = re.compile(r"^EFF-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
HISTORICAL_ID_RE = re.compile(r"^EHIST-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
AMENDMENT_ID_RE = re.compile(r"^EAMD-[0-9]{8}T[0-9]{6}Z-[A-F0-9]{8}$")
EPOCH_ID_RE = re.compile(r"^EPOCH-[0-9]{3,}$")


class ContractValidationError(RuntimeError):
    pass


def require_object(value: Any, label: str) -> dict:
    if not isinstance(value, dict):
        raise ContractValidationError(f"{label} must be an object")
    return value


def require_exact_fields(value: dict, *, required: set[str], allowed: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    if missing:
        raise ContractValidationError(f"{label} missing fields: " + ", ".join(missing))
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ContractValidationError(f"{label} unknown fields: " + ", ".join(unknown))


def require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractValidationError(f"{label} must be a non-empty string")
    return value.strip()


def require_datetime(value: Any, label: str) -> str:
    text = require_text(value, label)
    if not RFC3339_RE.fullmatch(text):
        raise ContractValidationError(f"{label} must be an RFC3339 date-time with timezone")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractValidationError(f"{label} is not a valid date-time") from exc
    if parsed.tzinfo is None:
        raise ContractValidationError(f"{label} must include a timezone")
    return text


def require_bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ContractValidationError(f"{label} must be boolean")
    return value


def require_int(value: Any, label: str, *, minimum: int | None = None) -> int:
    if type(value) is not int:
        raise ContractValidationError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ContractValidationError(f"{label} must be >= {minimum}")
    return value


def require_enum(value: Any, allowed: set[str], label: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ContractValidationError(f"invalid {label}")
    return value


def require_pattern(value: Any, pattern: re.Pattern[str], label: str) -> str:
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ContractValidationError(f"invalid {label}")
    return value


def require_sha256(value: Any, label: str) -> str:
    return require_pattern(value, SHA256_RE, label)


def require_unique_text_list(
    value: Any,
    label: str,
    *,
    min_items: int = 0,
    pattern: re.Pattern[str] | None = None,
) -> list[str]:
    if not isinstance(value, list) or len(value) < min_items:
        raise ContractValidationError(f"{label} must be an array with at least {min_items} item(s)")
    normalized: list[str] = []
    for item in value:
        text = require_text(item, f"{label} item")
        if pattern is not None and not pattern.fullmatch(text):
            raise ContractValidationError(f"invalid {label} item")
        normalized.append(text)
    if len(normalized) != len(set(normalized)):
        raise ContractValidationError(f"{label} items must be unique")
    return normalized


def validate_project(project: Any) -> None:
    value = require_object(project, "project")
    require_exact_fields(
        value,
        required={"repository"},
        allowed={"repository", "name"},
        label="project",
    )
    require_text(value["repository"], "project.repository")
    if "name" in value:
        require_text(value["name"], "project.name")


def validate_task_event_shape(event: Any) -> None:
    value = require_object(event, "task event")
    version = value.get("schema_version")
    if type(version) is not int:
        raise ContractValidationError("task event schema_version must be an integer")
    common_required = {
        "schema_version", "task_id", "recorded_at", "project", "framework_ref", "workflow",
        "risk", "terminal_state", "outcome_class", "material", "rework_cycles",
        "verification_failures", "verification_escape", "framework_feedback_created",
        "manual_workaround", "context_gap", "unexpected_scope_growth",
        "security_or_data_critical_event", "duration_class", "fingerprint",
    }
    optional = {"feedback_ids", "feedback_fingerprints", "tags"}
    if version == 1:
        required = common_required
        allowed = required | optional
    elif version == 2:
        required = common_required | {"occurrence_id", "signal_assessment", "failure_stage"}
        allowed = required | optional | {"task_group", "failure_subject"}
    else:
        raise ContractValidationError("unsupported task event schema_version")
    require_exact_fields(value, required=required, allowed=allowed, label="task event")
    require_pattern(value["task_id"], TASK_ID_RE, "task_id")
    require_datetime(value["recorded_at"], "recorded_at")
    validate_project(value["project"])
    require_text(value["framework_ref"], "framework_ref")
    require_text(value["workflow"], "workflow")
    require_enum(value["risk"], {"L0", "L1", "L2", "L3", "L4"}, "risk")
    require_text(value["terminal_state"], "terminal_state")
    require_enum(
        value["outcome_class"],
        {"verified_success", "success_with_deferred", "blocked", "failed", "canceled"},
        "outcome_class",
    )
    require_bool(value["material"], "material")
    require_int(value["rework_cycles"], "rework_cycles", minimum=0)
    require_int(value["verification_failures"], "verification_failures", minimum=0)
    for key in (
        "verification_escape", "framework_feedback_created", "manual_workaround", "context_gap",
        "unexpected_scope_growth", "security_or_data_critical_event",
    ):
        require_bool(value[key], key)
    require_enum(value["duration_class"], {"short", "medium", "long", "unknown"}, "duration_class")
    for key in ("feedback_ids", "tags"):
        if key in value:
            require_unique_text_list(value[key], key)
    if "feedback_fingerprints" in value:
        require_unique_text_list(value["feedback_fingerprints"], "feedback_fingerprints", pattern=SHA256_RE)
    require_sha256(value["fingerprint"], "fingerprint")

    if version == 2:
        require_pattern(value["occurrence_id"], OCCURRENCE_ID_RE, "occurrence_id")
        if "task_group" in value:
            require_text(value["task_group"], "task_group")
        require_enum(value["failure_stage"], {"none", "pre_merge", "post_merge", "runtime", "unknown"}, "failure_stage")
        if "failure_subject" in value:
            require_text(value["failure_subject"], "failure_subject")
        assessment = require_object(value["signal_assessment"], "signal_assessment")
        keys = {
            "rework_cycles", "verification_failures", "verification_escape",
            "framework_feedback_created", "manual_workaround", "context_gap",
            "unexpected_scope_growth", "security_or_data_critical_event",
        }
        require_exact_fields(assessment, required=keys, allowed=keys, label="signal_assessment")
        for key in keys:
            require_enum(assessment[key], {"measured", "not_assessed"}, f"signal_assessment.{key}")


def validate_learning_review_shape(review: Any) -> None:
    value = require_object(review, "learning review")
    version = value.get("schema_version")
    if type(version) is not int:
        raise ContractValidationError("learning review schema_version must be an integer")
    if version == 1:
        required = {
            "schema_version", "review_id", "closed_at", "epoch_id", "through_event_count",
            "trigger", "metrics", "findings", "decision", "evidence",
        }
        allowed = required | {"actions"}
    elif version == 2:
        required = {
            "schema_version", "review_id", "closed_at", "epoch_id", "reviewed_occurrence_ids",
            "event_digest", "trigger", "metrics", "findings", "decision", "evidence",
        }
        allowed = required | {"actions"}
    else:
        raise ContractValidationError("unsupported learning review schema_version")
    require_exact_fields(value, required=required, allowed=allowed, label="learning review")
    require_pattern(value["review_id"], REVIEW_ID_RE, "review_id")
    require_datetime(value["closed_at"], "closed_at")
    require_pattern(value["epoch_id"], EPOCH_ID_RE, "epoch_id")
    if version == 1:
        require_int(value["through_event_count"], "through_event_count", minimum=0)
    else:
        require_unique_text_list(value["reviewed_occurrence_ids"], "reviewed_occurrence_ids", min_items=1)
        require_sha256(value["event_digest"], "event_digest")
    trigger = require_object(value["trigger"], "trigger")
    require_exact_fields(trigger, required={"level", "reasons"}, allowed={"level", "reasons"}, label="trigger")
    require_enum(
        trigger["level"],
        {"INSUFFICIENT_EVIDENCE", "LEARNING_HEALTHY", "LEARNING_WATCH", "REVIEW_RECOMMENDED", "REVIEW_DUE", "IMMEDIATE_REVIEW"},
        "trigger.level",
    )
    require_unique_text_list(trigger["reasons"], "trigger.reasons")
    require_object(value["metrics"], "metrics")
    require_text(value["findings"], "findings")
    require_text(value["decision"], "decision")
    require_unique_text_list(value["evidence"], "evidence", min_items=1)
    if "actions" in value:
        require_unique_text_list(value["actions"], "actions")


def validate_feedback_event_shape(event: Any) -> None:
    value = require_object(event, "feedback event")
    version = value.get("schema_version")
    required = {
        "schema_version", "feedback_id", "recorded_at", "project", "framework_ref", "type",
        "severity", "observation", "evidence", "suggestion", "generalizability", "confidence",
        "status", "fingerprint",
    }
    optional = {"source_artifact", "negative_learning", "tags", "promotion_reference"}
    if version == 1:
        pass
    elif version == 2:
        required |= {"sensitivity_class", "redaction_state", "export_eligibility"}
    else:
        raise ContractValidationError("unsupported feedback schema_version")
    allowed = required | optional
    require_exact_fields(value, required=required, allowed=allowed, label="feedback event")
    require_pattern(value["feedback_id"], FEEDBACK_ID_RE, "feedback_id")
    require_datetime(value["recorded_at"], "recorded_at")
    validate_project(value["project"])
    require_text(value["framework_ref"], "framework_ref")
    require_enum(
        value["type"],
        {
            "architecture_gap", "workflow_gap", "skill_gap", "role_gap", "security_gap",
            "data_gap", "verification_gap", "runtime_gap", "performance_gap", "context_gap",
            "integration_gap", "false_positive", "false_negative", "process_friction",
            "missing_pattern", "documentation_gap",
        },
        "feedback type",
    )
    require_enum(value["severity"], {"low", "medium", "high", "critical"}, "severity")
    require_text(value["observation"], "observation")
    require_unique_text_list(value["evidence"], "evidence", min_items=1)
    require_text(value["suggestion"], "suggestion")
    require_enum(
        value["generalizability"],
        {"project_specific", "possible_generic", "likely_generic", "confirmed_multi_project"},
        "generalizability",
    )
    require_enum(value["confidence"], {"low", "medium", "high"}, "confidence")
    require_enum(value["status"], {"new", "triaged", "candidate", "promoted", "rejected", "archived"}, "status")
    if "source_artifact" in value:
        require_text(value["source_artifact"], "source_artifact")
    if "negative_learning" in value:
        require_text(value["negative_learning"], "negative_learning")
    if "tags" in value:
        require_unique_text_list(value["tags"], "tags")
    require_sha256(value["fingerprint"], "fingerprint")
    if version == 2:
        require_enum(value["sensitivity_class"], {"public", "internal", "confidential", "restricted"}, "sensitivity_class")
        require_enum(value["redaction_state"], {"not_required", "pending", "redacted", "approved"}, "redaction_state")
        require_enum(value["export_eligibility"], {"local_only", "review_required", "eligible"}, "export_eligibility")
        if value["export_eligibility"] == "eligible" and value["redaction_state"] not in {"not_required", "approved"}:
            raise ContractValidationError("eligible feedback must have approved/not-required redaction state")
    if value["status"] == "promoted":
        require_text(value.get("promotion_reference"), "promotion_reference")


def validate_runtime_adapter_shape(data: Any) -> None:
    value = require_object(data, "runtime adapter manifest")
    required = {"schema_version", "adapter_id", "display_name", "version", "status", "runtime_kind", "transport", "capabilities"}
    allowed = required | {"sources", "notes", "metadata"}
    require_exact_fields(value, required=required, allowed=allowed, label="runtime adapter manifest")
    if value["schema_version"] != 1:
        raise ContractValidationError("unsupported runtime adapter schema_version")
    require_pattern(value["adapter_id"], re.compile(r"^[a-z0-9][a-z0-9-]*$"), "adapter_id")
    require_text(value["display_name"], "display_name")
    require_text(value["version"], "version")
    require_enum(value["status"], {"experimental", "candidate", "stable", "deprecated"}, "status")
    require_text(value["runtime_kind"], "runtime_kind")
    require_enum(value["transport"], {"cli", "http", "rpc", "desktop-daemon", "native", "instructions"}, "transport")
    caps = require_unique_text_list(value["capabilities"], "capabilities")
    known = {
        "execute_task", "resume_session", "cancel_task", "read_workspace", "write_workspace",
        "shared_context", "artifact_handoff", "parallel_agents", "agent_handoff",
        "interactive_approval", "interactive_input", "tool_policy", "mutation_policy",
        "trace_export", "session_persistence", "runtime_recovery",
    }
    unknown = sorted(set(caps) - known)
    if unknown:
        raise ContractValidationError("unknown standardized capabilities: " + ", ".join(unknown))
    if "sources" in value:
        require_text(value["sources"], "sources")
    if "notes" in value and not isinstance(value["notes"], str):
        raise ContractValidationError("notes must be a string")
    if "metadata" in value:
        require_object(value["metadata"], "metadata")
    if value["status"] == "stable" and "sources" not in value:
        raise ContractValidationError("stable adapters require a sources reference")


def validate_retrospective_event_shape(event: Any) -> None:
    value = require_object(event, "retrospective event")
    version = value.get("schema_version")
    common_required = {
        "schema_version", "historical_event_id", "recorded_at", "observed_at", "project",
        "framework_ref_when_executed", "capture_mode", "evidence_quality", "task_label",
        "source_refs", "outcome_class", "signals", "fingerprint",
    }
    optional = {"workflow", "risk", "notes"}
    if version == 1:
        required = common_required
        allowed = required | optional
    elif version == 2:
        required = common_required | {"occurrence_id", "producer", "canonicalization_version"}
        allowed = required | optional
    else:
        raise ContractValidationError("unsupported retrospective schema_version")
    require_exact_fields(value, required=required, allowed=allowed, label="retrospective event")
    require_pattern(value["historical_event_id"], HISTORICAL_ID_RE, "historical_event_id")
    require_datetime(value["recorded_at"], "recorded_at")
    require_datetime(value["observed_at"], "observed_at")
    validate_project(value["project"])
    require_text(value["framework_ref_when_executed"], "framework_ref_when_executed")
    if value["capture_mode"] != "retrospective":
        raise ContractValidationError("capture_mode must be retrospective")
    require_enum(value["evidence_quality"], {"confirmed", "reconstructed", "inferred"}, "evidence_quality")
    require_text(value["task_label"], "task_label")
    if "workflow" in value:
        require_text(value["workflow"], "workflow")
    if "risk" in value:
        require_enum(value["risk"], {"L0", "L1", "L2", "L3", "L4", "UNKNOWN"}, "risk")
    require_unique_text_list(value["source_refs"], "source_refs", min_items=1)
    require_enum(value["outcome_class"], {"verified_success", "success_with_deferred", "blocked", "failed", "canceled", "unknown"}, "outcome_class")
    if not isinstance(value["signals"], list):
        raise ContractValidationError("signals must be an array")
    for index, signal in enumerate(value["signals"]):
        s = require_object(signal, f"signals[{index}]")
        require_exact_fields(s, required={"name", "value", "quality", "source_refs"}, allowed={"name", "value", "quality", "source_refs"}, label=f"signals[{index}]")
        name = require_enum(
            s["name"],
            {
                "rework_cycles", "verification_failures", "verification_escape", "manual_workaround",
                "context_gap", "unexpected_scope_growth", "security_or_data_critical_event",
                "framework_feedback_candidate",
            },
            f"signals[{index}].name",
        )
        if name in {"rework_cycles", "verification_failures"}:
            require_int(s["value"], f"signals[{index}].value", minimum=0)
        else:
            require_bool(s["value"], f"signals[{index}].value")
        require_enum(s["quality"], {"confirmed", "reconstructed", "inferred"}, f"signals[{index}].quality")
        require_unique_text_list(s["source_refs"], f"signals[{index}].source_refs", min_items=1)
    if "notes" in value:
        require_text(value["notes"], "notes")
    require_sha256(value["fingerprint"], "fingerprint")
    if version == 2:
        require_text(value["occurrence_id"], "occurrence_id")
        producer = require_object(value["producer"], "producer")
        require_exact_fields(
            producer,
            required={"repository", "ref", "schema_version", "canonicalization_version"},
            allowed={"repository", "ref", "schema_version", "canonicalization_version"},
            label="producer",
        )
        require_text(producer["repository"], "producer.repository")
        require_text(producer["ref"], "producer.ref")
        require_int(producer["schema_version"], "producer.schema_version", minimum=1)
        require_int(producer["canonicalization_version"], "producer.canonicalization_version", minimum=1)
        require_int(value["canonicalization_version"], "canonicalization_version", minimum=1)


def validate_retrospective_amendment_shape(amendment: Any) -> None:
    value = require_object(amendment, "retrospective amendment")
    required = {"schema_version", "amendment_id", "recorded_at", "occurrence_id", "reason", "changes", "producer"}
    require_exact_fields(value, required=required, allowed=required, label="retrospective amendment")
    if value["schema_version"] != 1:
        raise ContractValidationError("unsupported amendment schema_version")
    require_pattern(value["amendment_id"], AMENDMENT_ID_RE, "amendment_id")
    require_datetime(value["recorded_at"], "recorded_at")
    require_text(value["occurrence_id"], "occurrence_id")
    require_text(value["reason"], "reason")
    changes = require_object(value["changes"], "changes")
    allowed_changes = {"evidence_quality", "source_refs", "signals", "notes", "outcome_class"}
    unknown = sorted(set(changes) - allowed_changes)
    if unknown or not changes:
        raise ContractValidationError("changes must contain only supported non-identity fields")
    producer = require_object(value["producer"], "producer")
    require_exact_fields(producer, required={"repository", "ref"}, allowed={"repository", "ref"}, label="producer")
    require_text(producer["repository"], "producer.repository")
    require_text(producer["ref"], "producer.ref")
