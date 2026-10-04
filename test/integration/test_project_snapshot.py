"""Check the pinned source snapshot and its installed ROS metadata together."""

import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from ament_index_python.packages import get_package_share_directory
from snapshot_support import COMPONENT_NAMES, load_snapshot

SOURCE = Path(os.environ["RV2_PROJECT_SOURCE_DIR"])
SHARE = Path(os.environ["RV2_PROJECT_SHARE_DIR"])
# These workspace additions do not change the historical schema 1 snapshots.
WORKSPACE_CONSUMERS = (
    (
        "rv2_csm_topic_bridge",
        "0.1.0",
        "78ba1a94825eb9790f23a3be5dbfb31df5162ec7",
        "c3f2b4b6dc669d98552b801b5bc68858aec4da61",
    ),
    (
        "rv2_server_control",
        "0.1.1",
        "38cfa0f233eb1343e77b54ae97790d01171118fc",
        "c3a2794e5c49c1ab35288d012db3777f273d0d32",
    ),
)
JOY_INTERPRETER_COMMIT = "fb09f704c1c3789b3ce8c2521bd4b6e339e932ea"


def git(repository, *arguments):
    """Read this mounted repository without changing global Git configuration."""
    return subprocess.check_output(
        [
            "git",
            "-c",
            f"safe.directory={repository}",
            "-C",
            str(repository),
            *arguments,
        ],
        text=True,
        stderr=subprocess.STDOUT,
        timeout=20,
    ).strip()


@pytest.fixture(scope="module")
def snapshot():
    version = ET.parse(SOURCE / "package.xml").getroot().findtext("version")
    return load_snapshot(SOURCE / "snapshots" / f"v{version}.json", version)


@pytest.mark.parametrize("name", COMPONENT_NAMES)
def test_component_release_matches_gitlink_checkout_and_version(snapshot, name):
    component = snapshot["components"][name]
    repository = SOURCE / component["path"]
    expected = component["commit"]
    entry = git(SOURCE, "ls-tree", "HEAD", "--", component["path"]).split()
    assert entry == ["160000", "commit", expected, component["path"]]
    assert git(repository, "rev-parse", "HEAD") == expected
    assert git(repository, "status", "--porcelain", "--untracked-files=all") == ""
    assert git(repository, "rev-parse", "HEAD^{tree}") == component["tree"]
    tag = f"refs/tags/v{component['version']}"
    assert git(repository, "rev-parse", tag + "^{commit}") == component["tag_commit"]
    assert git(repository, "rev-parse", tag + "^{tree}") == component["tree"]
    assert git(repository, "remote", "get-url", "origin") == component["repository"]
    assert (
        git(
            SOURCE,
            "config",
            "--file",
            ".gitmodules",
            "--get",
            f"submodule.{component['path']}.url",
        )
        == component["repository"]
    )
    if name == "r1_test_framework":
        assert (repository / "VERSION").read_text().strip() == component["version"]
    else:
        package = ET.parse(repository / "package.xml").getroot()
        assert package.findtext("name") == name
        assert package.findtext("version") == component["version"]


def test_project_framework_matches_workspace_framework(snapshot):
    component = snapshot["components"]["r1_test_framework"]
    framework = SOURCE / "r1_test_framework"
    assert git(SOURCE, "ls-tree", "HEAD", "r1_test_framework").split() == [
        "160000",
        "commit",
        component["commit"],
        "r1_test_framework",
    ]
    assert git(framework, "rev-parse", "HEAD") == component["commit"]
    assert git(framework, "status", "--porcelain", "--untracked-files=all") == ""
    assert (framework / "VERSION").read_text().strip() == component["version"]
    assert (framework / "COLCON_IGNORE").is_file()
    assert (
        git(
            SOURCE, "config", "--file", ".gitmodules", "submodule.r1_test_framework.url"
        )
        == component["repository"]
    )


@pytest.mark.parametrize("name,version,commit,tag_commit", WORKSPACE_CONSUMERS)
def test_workspace_consumers_match_merged_releases_and_framework(
    snapshot, name, version, commit, tag_commit
):
    """Validate added consumers without widening an immutable snapshot."""
    relative = f"ros2_ws/src/{name}"
    repository = SOURCE / relative
    origin = f"git@github.com:cocobird231/{name}.git"
    assert git(SOURCE, "ls-tree", "HEAD", "--", relative).split() == [
        "160000",
        "commit",
        commit,
        relative,
    ]
    assert git(repository, "rev-parse", "HEAD") == commit
    assert git(repository, "status", "--porcelain", "--untracked-files=all") == ""
    assert git(repository, "remote", "get-url", "origin") == origin
    for field, expected in (("url", origin), ("branch", "r1")):
        assert (
            git(
                SOURCE,
                "config",
                "--file",
                ".gitmodules",
                "--get",
                f"submodule.{relative}.{field}",
            )
            == expected
        )
    package = ET.parse(repository / "package.xml").getroot()
    assert package.findtext("name") == name
    assert package.findtext("version") == version
    tag = f"refs/tags/v{version}"
    assert git(repository, "rev-parse", tag + "^{commit}") == tag_commit
    assert git(repository, "rev-parse", tag + "^{tree}") == git(
        repository, "rev-parse", "HEAD^{tree}"
    )

    framework = snapshot["components"]["r1_test_framework"]
    nested = repository / "r1_test_framework"
    assert git(repository, "ls-tree", "HEAD", "r1_test_framework").split() == [
        "160000",
        "commit",
        framework["commit"],
        "r1_test_framework",
    ]
    root_framework_commit = git(SOURCE / "r1_test_framework", "rev-parse", "HEAD")
    assert root_framework_commit == framework["commit"]
    assert git(nested, "rev-parse", "HEAD") == root_framework_commit
    assert git(nested, "status", "--porcelain", "--untracked-files=all") == ""
    assert git(nested, "remote", "get-url", "origin") == framework["repository"]
    assert (
        git(
            repository,
            "config",
            "--file",
            ".gitmodules",
            "submodule.r1_test_framework.url",
        )
        == framework["repository"]
    )


def test_joy_interpreter_matches_pinned_source_dependency():
    """Check the source pin without requiring a release tag or test framework."""
    relative = "ros2_ws/src/joy_interpreter"
    repository = SOURCE / relative
    origin = "git@github.com:cocobird231/joy_interpreter.git"
    assert git(SOURCE, "ls-tree", "HEAD", "--", relative).split() == [
        "160000",
        "commit",
        JOY_INTERPRETER_COMMIT,
        relative,
    ]
    assert git(repository, "rev-parse", "HEAD") == JOY_INTERPRETER_COMMIT
    assert git(repository, "status", "--porcelain", "--untracked-files=all") == ""
    assert git(repository, "remote", "get-url", "origin") == origin
    for field, expected in (("path", relative), ("url", origin)):
        assert (
            git(
                SOURCE,
                "config",
                "--file",
                ".gitmodules",
                "--get",
                f"submodule.{relative}.{field}",
            )
            == expected
        )
    package = ET.parse(repository / "package.xml").getroot()
    assert package.findtext("name") == "joy_interpreter"
    assert package.findtext("version") == "0.1.0"


def test_installed_package_is_discoverable_and_metadata_matches(snapshot):
    assert Path(get_package_share_directory("rv2_project")) == SHARE
    assert (SHARE / "package.xml").read_bytes() == (SOURCE / "package.xml").read_bytes()
    assert (SHARE / "README.md").read_bytes() == (SOURCE / "README.md").read_bytes()
    launch_file = Path("launch/test_joystick.launch.py")
    assert (SHARE / launch_file).read_bytes() == (SOURCE / launch_file).read_bytes()
    installed = load_snapshot(
        SHARE / "snapshots" / f"v{snapshot['project_version']}.json",
        snapshot["project_version"],
    )
    assert installed == snapshot
    for relative in ("ros2_ws", "r1_test_framework", "test_env", ".git"):
        assert not (SHARE / relative).exists()
    source_files = sorted((SOURCE / "docs").rglob("*.md"))
    assert source_files
    for source in source_files:
        assert (SHARE / source.relative_to(SOURCE)).read_bytes() == source.read_bytes()


def test_design_records_every_snapshot_version_and_commit(snapshot):
    design = (SOURCE / "docs/r1_design_docs/r1_design_draft.md").read_text()
    names = [
        "r1_test_framework",
        "r1_interfaces",
        "r1_test_mocks",
        "r1_integration_tests",
        "rv2_control_signal_transport",
    ]
    for path in sorted((SOURCE / "snapshots").glob("v*.json")):
        record = load_snapshot(path, path.stem[1:])
        versions = [f"v{record['project_version']}"] + [
            f"v{record['components'][name]['version']}" for name in names
        ]
        assert "| " + " | ".join(versions) + " |" in design
        for name, component in record["components"].items():
            row = f"| {name} | {component['commit']} | {component['tag_commit']} |"
            assert row in design
    assert snapshot["acceptance"] == "pending"
    assert snapshot["limitations"]


def test_colcon_owner_and_explicit_workspace_discovery():
    owner = subprocess.check_output(
        ["colcon", "list", "--base-paths", str(SOURCE), "--names-only"],
        text=True,
        timeout=30,
    ).splitlines()
    assert owner == ["rv2_project"]
    # External source dependencies may also live here; check managed components.
    names = (
        *COMPONENT_NAMES,
        *(name for name, _, _, _ in WORKSPACE_CONSUMERS),
        "joy_interpreter",
    )
    children = [str(SOURCE / "ros2_ws/src" / name) for name in names]
    workspace = subprocess.check_output(
        ["colcon", "list", "--paths", str(SOURCE), *children, "--names-only"],
        text=True,
        timeout=30,
    ).splitlines()
    assert set(workspace) == {
        "rv2_project",
        "r1_interfaces",
        "r1_test_mocks",
        "r1_integration_tests",
        "rv2_control_signal_transport",
        "rv2_csm_topic_bridge",
        "rv2_server_control",
        "joy_interpreter",
    }
    assert len(workspace) == 8
