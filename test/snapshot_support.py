"""Validate the development snapshot manifest used by project tests."""

import json
import re
from pathlib import Path

COMPONENT_NAMES = (
    "r1_test_framework",
    "r1_interfaces",
    "r1_test_mocks",
    "r1_integration_tests",
    "rv2_control_signal_transport",
)
_SNAPSHOT_FIELDS = {
    "schema_version",
    "project_version",
    "status",
    "acceptance",
    "limitations",
    "components",
}
_COMPONENT_FIELDS = {
    "path",
    "repository",
    "branch",
    "version",
    "commit",
    "tag_commit",
    "tree",
}
_VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
_HASH = re.compile(r"[0-9a-f]{40}")


def _require_fields(value, fields, label):
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f"{label} must contain exactly the required fields")


def _require_version(value, label):
    if not isinstance(value, str) or _VERSION.fullmatch(value) is None:
        raise ValueError(f"{label} must be a canonical X.Y.Z version")


def validate_snapshot(data, expected_version):
    """Reject malformed manifests and mismatches with the package version."""
    _require_version(expected_version, "expected_version")
    _require_fields(data, _SNAPSHOT_FIELDS, "snapshot")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("schema_version must be the integer 1")
    _require_version(data["project_version"], "project_version")
    if data["project_version"] != expected_version:
        raise ValueError("project_version must match the package version")
    if data["status"] != "development":
        raise ValueError("status must be development")
    if data["acceptance"] != "pending":
        raise ValueError("acceptance must be pending")
    limitations = data["limitations"]
    if (
        not isinstance(limitations, list)
        or not limitations
        or any(not isinstance(item, str) or not item.strip() for item in limitations)
    ):
        raise ValueError("limitations must be a nonempty list of nonblank strings")

    _require_fields(data["components"], COMPONENT_NAMES, "components")
    for name, component in data["components"].items():
        _require_fields(component, _COMPONENT_FIELDS, name)
        if component["path"] != f"ros2_ws/src/{name}":
            raise ValueError(f"{name}.path must be its exact project-relative path")
        if component["repository"] != f"git@github.com:cocobird231/{name}.git":
            raise ValueError(
                f"{name}.repository must identify its component repository"
            )
        branch = "r1" if name == "rv2_control_signal_transport" else "master"
        if component["branch"] != branch:
            raise ValueError(f"{name}.branch must be {branch}")
        _require_version(component["version"], f"{name}.version")
        for field in ("commit", "tag_commit", "tree"):
            value = component[field]
            if not isinstance(value, str) or _HASH.fullmatch(value) is None:
                raise ValueError(f"{name}.{field} must be a lowercase 40-digit hex SHA")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_snapshot(path, expected_version):
    """Read and validate JSON, preserving I/O errors and rejecting duplicate keys."""
    with Path(path).open(encoding="utf-8") as source:
        data = json.load(source, object_pairs_hook=_unique_object)
    validate_snapshot(data, expected_version)
    return data
