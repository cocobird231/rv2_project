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


def test_installed_package_is_discoverable_and_metadata_matches(snapshot):
    assert Path(get_package_share_directory("rv2_project")) == SHARE
    assert (SHARE / "package.xml").read_bytes() == (SOURCE / "package.xml").read_bytes()
    assert (SHARE / "README.md").read_bytes() == (SOURCE / "README.md").read_bytes()
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
    children = [str(path) for path in sorted((SOURCE / "ros2_ws/src").iterdir())]
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
    }
    assert len(workspace) == 5
