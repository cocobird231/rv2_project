"""Exercise the pre-install contract with recorded external tool invocations."""

import json
import os
import pathlib
import shlex
import shutil
import subprocess

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "pre_install.sh"
PACKAGES = ("unitree_api", "unitree_go", "unitree_hg")
TOOL_STUB = """#!/usr/bin/env python3
import json
import os
import pathlib
import sys

name = pathlib.Path(sys.argv[0]).name
with open(os.environ["PREINSTALL_TRACE"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps([name, sys.argv[1:]]) + "\\n")
code = int(os.environ.get("PREINSTALL_" + name.upper() + "_EXIT", "0"))
if name == "colcon" and code == 0:
    prefix = pathlib.Path(sys.argv[sys.argv.index("--install-base") + 1])
    prefix.mkdir(parents=True, exist_ok=True)
    (prefix / "setup.bash").write_text("# test underlay\\n")
sys.exit(code)
"""


@pytest.fixture
def project(tmp_path, monkeypatch):
    """Prepare a source tree with spaces and instrument only dependency/build tools."""
    root = tmp_path / "project with spaces"
    root.mkdir()
    shutil.copyfile(SCRIPT, root / "pre_install.sh")
    vendor = root / "ros2_ws/src/rv2_server_control/thirdparty/unitree"
    for name in PACKAGES:
        package = vendor / name
        package.mkdir(parents=True)
        (package / "package.xml").write_text(
            f"<package><name>{name}</name></package>\n"
        )
        (package / "CMakeLists.txt").write_text(f"project({name})\n")
    (vendor / "LICENSE").write_text("BSD 3-Clause License test fixture\n")
    tools = tmp_path / "tools"
    tools.mkdir()
    for name in ("colcon", "rosdep"):
        command = tools / name
        command.write_text(TOOL_STUB)
        command.chmod(0o755)
    caller = tmp_path / "caller"
    caller.mkdir()
    monkeypatch.chdir(caller)
    monkeypatch.setenv("PATH", str(tools) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("ROS_VERSION", "2")
    monkeypatch.setenv("ROS_DISTRO", "jazzy")
    monkeypatch.setenv("PREINSTALL_TRACE", str(tmp_path / "trace.jsonl"))
    monkeypatch.delenv("PREINSTALL_ROSDEP_EXIT", raising=False)
    monkeypatch.delenv("PREINSTALL_COLCON_EXIT", raising=False)
    return root


def invoke(project, *arguments):
    """Run the real shell entry point while external tools remain controlled."""
    return subprocess.run(
        ["bash", str(project / "pre_install.sh"), *arguments],
        text=True,
        capture_output=True,
        timeout=10,
    )


def calls():
    """Read actual subprocess argument boundaries from the tool stubs."""
    trace = pathlib.Path(os.environ["PREINSTALL_TRACE"])
    return (
        [json.loads(line) for line in trace.read_text().splitlines()]
        if trace.exists()
        else []
    )


def test_default_installs_all_bundled_packages_and_preserves_license(project):
    """Use fixed source roots independently of cwd and produce a sourceable underlay."""
    result = invoke(project)
    assert result.returncode == 0, result.stderr
    recorded = calls()
    assert [name for name, _ in recorded] == ["rosdep", "colcon"]
    vendor = project / "ros2_ws/src/rv2_server_control/thirdparty/unitree"
    paths = [str(vendor / name) for name in PACKAGES]
    rosdep = recorded[0][1]
    assert (
        rosdep[rosdep.index("--from-paths") + 1 : rosdep.index("--ignore-src")] == paths
    )
    assert rosdep[rosdep.index("--rosdistro") + 1] == "jazzy"
    assert [rosdep[i + 1] for i, value in enumerate(rosdep) if value == "-t"] == [
        "build",
        "buildtool",
        "build_export",
        "buildtool_export",
        "exec",
    ]
    colcon = recorded[1][1]
    assert (
        colcon[colcon.index("--base-paths") + 1 : colcon.index("--build-base")] == paths
    )
    assert colcon[
        colcon.index("--packages-select") + 1 : colcon.index("--cmake-args")
    ] == list(PACKAGES)
    assert "--merge-install" in colcon
    assert "-DBUILD_TESTING=OFF" in colcon
    output = project / "pre_install/jazzy"
    assert (output / "COLCON_IGNORE").is_file()
    for name in PACKAGES:
        assert (output / f"install/share/{name}/LICENSE").read_bytes() == (
            vendor / "LICENSE"
        ).read_bytes()
    assert shlex.split(result.stdout.splitlines()[-1]) == [
        "source",
        str(output / "install/setup.bash"),
    ]


def test_relative_output_is_resolved_from_caller(project):
    """A custom output directory does not write into the project checkout."""
    output = pathlib.Path.cwd() / "custom underlay"
    result = invoke(project, "--output-dir", "custom underlay")
    assert result.returncode == 0, result.stderr
    colcon = calls()[1][1]
    assert colcon[colcon.index("--install-base") + 1] == str(output / "install")
    assert (output / "COLCON_IGNORE").is_file()
    assert not (project / "pre_install").exists()


def test_dry_run_does_not_run_tools_or_write_output(project):
    """Planning must not install dependencies, invoke colcon, or create files."""
    result = invoke(project, "--dry-run")
    assert result.returncode == 0, result.stderr
    assert calls() == []
    assert not (project / "pre_install").exists()
    assert "rosdep install" in result.stdout
    assert "colcon --log-base" in result.stdout


@pytest.mark.parametrize("tool, code", [("ROSDEP", 17), ("COLCON", 23)])
def test_failure_propagates_without_claiming_success(project, monkeypatch, tool, code):
    """Stop on dependency failure and preserve errors from either external tool."""
    monkeypatch.setenv(f"PREINSTALL_{tool}_EXIT", str(code))
    result = invoke(project)
    assert result.returncode == code
    assert "Source the Unitree underlay" not in result.stdout
    assert [name for name, _ in calls()] == (
        ["rosdep"] if tool == "ROSDEP" else ["rosdep", "colcon"]
    )


def test_missing_bundle_fails_before_installing_dependencies(project):
    """An incomplete submodule checkout must never start dependency installation."""
    (
        project
        / "ros2_ws/src/rv2_server_control/thirdparty/unitree/unitree_hg/package.xml"
    ).unlink()
    result = invoke(project)
    assert result.returncode == 2
    assert "Missing bundled package" in result.stderr
    assert calls() == []


def test_unsourced_ros_environment_fails_before_tools(project, monkeypatch):
    """A missing ROS environment must not guess a distro or install host packages."""
    monkeypatch.delenv("ROS_DISTRO")
    result = invoke(project)
    assert result.returncode == 2
    assert "Source a ROS 2 environment" in result.stderr
    assert calls() == []


@pytest.mark.parametrize(
    "target", [".", "..", "/", "ros2_ws/src", "ros2_ws/src/rv2_server_control"]
)
def test_output_cannot_hide_source_packages(project, target):
    """Reject paths where COLCON_IGNORE would exclude the project or its sources."""
    result = invoke(project, "--output-dir", str(project / target))
    assert result.returncode == 2
    assert "must not contain or be inside" in result.stderr
    assert calls() == []
    assert not (project / "COLCON_IGNORE").exists()
