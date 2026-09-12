"""Exercise snapshot schema validation independently of live Git checkouts."""

import copy
import json

import pytest
from snapshot_support import load_snapshot, validate_snapshot


@pytest.fixture
def snapshot():
    names = (
        "r1_test_framework",
        "r1_interfaces",
        "r1_test_mocks",
        "r1_integration_tests",
        "rv2_control_signal_transport",
    )
    return {
        "schema_version": 1,
        "project_version": "0.1.0",
        "status": "development",
        "acceptance": "pending",
        "limitations": ["Runtime acceptance is pending."],
        "components": {
            name: {
                "path": f"ros2_ws/src/{name}",
                "repository": f"git@github.com:cocobird231/{name}.git",
                "branch": "r1" if name == "rv2_control_signal_transport" else "master",
                "version": "0.5.0" if name == "r1_test_framework" else "0.1.1",
                "commit": "a" * 40,
                "tag_commit": "b" * 40,
                "tree": "0123456789abcdef" * 2 + "01234567",
            }
            for name in names
        },
    }


def test_valid_snapshot_is_not_modified(snapshot):
    original = copy.deepcopy(snapshot)
    assert validate_snapshot(snapshot, "0.1.0") is None
    assert snapshot == original


@pytest.mark.parametrize("version", ["0.0.0", "1.0.0", "12.34.56"])
def test_canonical_project_versions(snapshot, version):
    snapshot["project_version"] = version
    assert validate_snapshot(snapshot, version) is None


@pytest.mark.parametrize("value", [None, [], "snapshot", 1, True])
def test_reject_non_object_snapshot(value):
    with pytest.raises(ValueError, match="snapshot"):
        validate_snapshot(value, "0.1.0")


@pytest.mark.parametrize(
    "field",
    [
        "schema_version",
        "project_version",
        "status",
        "acceptance",
        "limitations",
        "components",
    ],
)
def test_reject_missing_top_level_field(snapshot, field):
    del snapshot[field]
    with pytest.raises(ValueError, match="snapshot"):
        validate_snapshot(snapshot, "0.1.0")


def test_reject_unknown_top_level_field(snapshot):
    snapshot["unknown"] = "value"
    with pytest.raises(ValueError, match="snapshot"):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize("value", [True, False, 1.0, "1", 0, 2, None])
def test_reject_unsupported_schema_version(snapshot, value):
    snapshot["schema_version"] = value
    with pytest.raises(ValueError, match="schema_version"):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize(
    "version",
    [
        None,
        True,
        1,
        "",
        "v0.1.0",
        "01.1.0",
        "0.01.0",
        "0.1.00",
        "0.1",
        "0.1.0\n",
        "0.1.0-rc1",
    ],
)
@pytest.mark.parametrize("field", ["project_version", "expected_version", "component"])
def test_reject_noncanonical_version(snapshot, version, field):
    expected = "0.1.0"
    if field == "component":
        snapshot["components"]["r1_interfaces"]["version"] = version
    elif field == "expected_version":
        expected = version
    else:
        snapshot[field] = version
    with pytest.raises(ValueError, match="version"):
        validate_snapshot(snapshot, expected)


def test_reject_package_version_mismatch(snapshot):
    with pytest.raises(ValueError, match="project_version"):
        validate_snapshot(snapshot, "0.2.0")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("status", "release"),
        ("status", None),
        ("acceptance", "passed"),
        ("acceptance", False),
    ],
)
def test_reject_unsupported_status(snapshot, field, value):
    snapshot[field] = value
    with pytest.raises(ValueError, match=field):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize(
    "value", [None, "pending", [], [""], [" \t\n"], [1], ["valid", None]]
)
def test_reject_missing_or_invalid_limitations(snapshot, value):
    snapshot["limitations"] = value
    with pytest.raises(ValueError, match="limitations"):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize("value", [None, [], "components", {}])
def test_reject_invalid_components(snapshot, value):
    snapshot["components"] = value
    with pytest.raises(ValueError, match="components"):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize(
    "name",
    [
        "r1_test_framework",
        "r1_interfaces",
        "r1_test_mocks",
        "r1_integration_tests",
        "rv2_control_signal_transport",
    ],
)
def test_reject_missing_component(snapshot, name):
    del snapshot["components"][name]
    with pytest.raises(ValueError, match="components"):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize("replace_existing", [False, True])
def test_reject_unknown_component(snapshot, replace_existing):
    component = snapshot["components"]["r1_interfaces"]
    if replace_existing:
        del snapshot["components"]["r1_interfaces"]
    snapshot["components"]["unknown_package"] = component
    with pytest.raises(ValueError, match="components"):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize("value", [None, [], "component", {}])
def test_reject_non_object_component(snapshot, value):
    snapshot["components"]["r1_interfaces"] = value
    with pytest.raises(ValueError, match="r1_interfaces"):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize(
    "field", ["path", "repository", "branch", "version", "commit", "tag_commit", "tree"]
)
def test_reject_missing_component_field(snapshot, field):
    del snapshot["components"]["r1_interfaces"][field]
    with pytest.raises(ValueError, match="r1_interfaces"):
        validate_snapshot(snapshot, "0.1.0")


def test_reject_unknown_component_field(snapshot):
    snapshot["components"]["r1_interfaces"]["unknown"] = "value"
    with pytest.raises(ValueError, match="r1_interfaces"):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize(
    "value",
    [
        None,
        "r1_interfaces",
        "/ros2_ws/src/r1_interfaces",
        "ros2_ws/src/../r1_interfaces",
        "ros2_ws/src/r1_test_mocks",
    ],
)
def test_reject_wrong_component_path(snapshot, value):
    snapshot["components"]["r1_interfaces"]["path"] = value
    with pytest.raises(ValueError, match="path"):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize(
    "value",
    [
        None,
        "https://github.com/cocobird231/r1_interfaces.git",
        "git@github.com:other/r1_interfaces.git",
    ],
)
def test_reject_wrong_repository(snapshot, value):
    snapshot["components"]["r1_interfaces"]["repository"] = value
    with pytest.raises(ValueError, match="repository"):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize(
    ("name", "branch"),
    [
        ("r1_interfaces", "r1"),
        ("rv2_control_signal_transport", "master"),
        ("r1_test_framework", None),
    ],
)
def test_reject_wrong_component_branch(snapshot, name, branch):
    snapshot["components"][name]["branch"] = branch
    with pytest.raises(ValueError, match="branch"):
        validate_snapshot(snapshot, "0.1.0")


@pytest.mark.parametrize("field", ["commit", "tag_commit", "tree"])
@pytest.mark.parametrize(
    "value", [None, 1, "a" * 39, "a" * 41, "A" * 40, "g" * 40, "a" * 40 + "\n"]
)
def test_reject_invalid_hash(snapshot, field, value):
    snapshot["components"]["r1_interfaces"][field] = value
    with pytest.raises(ValueError, match=field):
        validate_snapshot(snapshot, "0.1.0")


def test_load_valid_snapshot(snapshot, tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    assert load_snapshot(path, "0.1.0") == snapshot


@pytest.mark.parametrize(
    "contents",
    [
        '{"schema_version": 1, "schema_version": 1}',
        '{"components": {"r1_interfaces": {}, "r1_interfaces": {}}}',
        '{"components": {"r1_interfaces": {"commit": "a", "commit": "a"}}}',
    ],
)
def test_load_rejects_duplicate_keys(tmp_path, contents):
    path = tmp_path / "snapshot.json"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        load_snapshot(path, "0.1.0")


def test_load_rejects_invalid_json(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_snapshot(path, "0.1.0")


def test_load_validates_manifest(snapshot, tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(snapshot), encoding="utf-8")
    with pytest.raises(ValueError, match="project_version"):
        load_snapshot(path, "0.2.0")


def test_load_missing_file_fails(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_snapshot(tmp_path / "missing.json", "0.1.0")


def test_load_directory_fails(tmp_path):
    with pytest.raises(IsADirectoryError):
        load_snapshot(tmp_path, "0.1.0")
