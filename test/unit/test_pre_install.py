"""Exercise the pre-install contract with recorded external tool invocations."""

import json
import os
import pathlib
import shlex
import shutil
import subprocess

import pytest
from rosdep2 import sources_list

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "pre_install.sh"
PACKAGES = ("unitree_api", "unitree_go", "unitree_hg")
TOOL_STUB = """#!/usr/bin/env python3
import json
import os
import pathlib
import sys

name = pathlib.Path(sys.argv[0]).name
if name == "id":
    assert sys.argv[1:] == ["-u"]
    print(os.environ.get("PREINSTALL_UID", "0"))
    sys.exit(0)
with open(os.environ["PREINSTALL_TRACE"], "a", encoding="utf-8") as stream:
    stream.write(json.dumps([name, sys.argv[1:]]) + "\\n")
if name == "sudo":
    os.environ["PREINSTALL_THROUGH_SUDO"] = "1"
    os.execvp(sys.argv[1], sys.argv[1:])
code = int(os.environ.get("PREINSTALL_" + name.upper() + "_EXIT", "0"))
if name == "rosdep":
    verb = sys.argv[1]
    code = int(os.environ.get("PREINSTALL_ROSDEP_" + verb.upper() + "_EXIT", code))
    if verb == "update" and os.environ.get("PREINSTALL_THROUGH_SUDO"):
        sys.exit(91)
    if code == 0 and verb == "init":
        directory = pathlib.Path(os.environ["ROSDEP_SOURCE_PATH"].split(os.pathsep)[0])
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "20-default.list").write_text("yaml https://example.test/default.yaml\\n")
    if code == 0 and verb == "update":
        from rosdep2 import sources_list
        cache = pathlib.Path(sources_list.get_sources_cache_dir()) / sources_list.CACHE_INDEX
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text("test cache\\n")
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
    for name in ("colcon", "rosdep", "id", "sudo"):
        command = tools / name
        command.write_text(TOOL_STUB)
        command.chmod(0o755)
    caller = tmp_path / "caller"
    caller.mkdir()
    monkeypatch.chdir(caller)
    monkeypatch.setenv("PATH", str(tools) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("ROS_VERSION", "2")
    monkeypatch.setenv("ROS_DISTRO", "jazzy")
    sources = tmp_path / "custom rosdep sources"
    sources.mkdir()
    (sources / "50-custom.list").write_text("yaml https://example.test/custom.yaml\n")
    monkeypatch.setenv("ROSDEP_SOURCE_PATH", str(sources))
    monkeypatch.setenv("ROS_HOME", str(tmp_path / "ros home"))
    cache = cache_index()
    cache.parent.mkdir(parents=True)
    cache.write_text("existing cache\n")
    monkeypatch.setenv("PREINSTALL_TRACE", str(tmp_path / "trace.jsonl"))
    monkeypatch.setenv("PREINSTALL_UID", "0")
    monkeypatch.delenv("PREINSTALL_ROSDEP_EXIT", raising=False)
    monkeypatch.delenv("PREINSTALL_COLCON_EXIT", raising=False)
    monkeypatch.delenv("PREINSTALL_THROUGH_SUDO", raising=False)
    for verb in ("INIT", "UPDATE", "INSTALL"):
        monkeypatch.delenv(f"PREINSTALL_ROSDEP_{verb}_EXIT", raising=False)
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


def cache_index():
    """Locate the caller's cache through the installed rosdep API."""
    return pathlib.Path(sources_list.get_sources_cache_dir()) / sources_list.CACHE_INDEX


def require_bootstrap(*, missing_sources=False):
    """Remove only fixture state to model a fresh user or uninitialized rosdep."""
    cache_index().unlink(missing_ok=True)
    if missing_sources:
        for directory in os.environ["ROSDEP_SOURCE_PATH"].split(os.pathsep):
            for path in pathlib.Path(directory).glob("*.list"):
                path.unlink()


def rosdep_files():
    """Record configuration and cache bytes to detect dry-run mutations."""
    return {
        str(path): path.read_bytes()
        for root in [
            *os.environ["ROSDEP_SOURCE_PATH"].split(os.pathsep),
            os.environ["ROS_HOME"],
        ]
        for path in pathlib.Path(root).rglob("*")
        if path.is_file()
    }


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


@pytest.mark.parametrize("uid", ["0", "1001"])
def test_missing_sources_init_then_update_as_current_user(project, monkeypatch, uid):
    """Initialize once, elevate only init when needed, then fill the user's cache."""
    require_bootstrap(missing_sources=True)
    monkeypatch.setenv("PREINSTALL_UID", uid)
    result = invoke(project)
    assert result.returncode == 0, result.stderr
    recorded = calls()
    if uid != "0":
        assert recorded.pop(0) == [
            "sudo",
            [
                "env",
                f"ROSDEP_SOURCE_PATH={os.environ['ROSDEP_SOURCE_PATH']}",
                "rosdep",
                "init",
            ],
        ]
    assert [name for name, _ in recorded] == ["rosdep", "rosdep", "rosdep", "colcon"]
    assert recorded[0] == ["rosdep", ["init"]]
    assert recorded[1] == ["rosdep", ["update", "--rosdistro", "jazzy"]]
    assert recorded[2][1][0] == "install"
    assert cache_index().is_file()
    assert (
        pathlib.Path(os.environ["ROSDEP_SOURCE_PATH"]) / "20-default.list"
    ).is_file()


def test_existing_custom_sources_only_update_missing_user_cache(project, monkeypatch):
    """Keep user source files intact and update without privilege escalation."""
    require_bootstrap()
    monkeypatch.setenv("PREINSTALL_UID", "1001")
    existing = os.environ["ROSDEP_SOURCE_PATH"]
    before = rosdep_files()
    result = invoke(project)
    assert result.returncode == 0, result.stderr
    recorded = calls()
    assert recorded[0] == ["rosdep", ["update", "--rosdistro", "jazzy"]]
    assert [name for name, _ in recorded] == ["rosdep", "rosdep", "colcon"]
    assert recorded[1][1][0] == "install"
    assert cache_index().is_file()
    assert not (pathlib.Path(existing) / "20-default.list").exists()
    assert all(pathlib.Path(path).read_bytes() == data for path, data in before.items())


def test_existing_cache_does_not_reinitialize_missing_source_lists(project):
    """A usable cached environment does not require rewriting system sources."""
    for path in pathlib.Path(os.environ["ROSDEP_SOURCE_PATH"]).glob("*.list"):
        path.unlink()
    result = invoke(project)
    assert result.returncode == 0, result.stderr
    assert [name for name, _ in calls()] == ["rosdep", "colcon"]
    assert calls()[0][1][0] == "install"


def test_relative_output_is_resolved_from_caller(project):
    """A custom output directory does not write into the project checkout."""
    output = pathlib.Path.cwd() / "custom underlay"
    result = invoke(project, "--output-dir", "custom underlay")
    assert result.returncode == 0, result.stderr
    colcon = calls()[1][1]
    assert colcon[colcon.index("--install-base") + 1] == str(output / "install")
    assert (output / "COLCON_IGNORE").is_file()
    assert not (project / "pre_install").exists()


@pytest.mark.parametrize("state", ["ready", "missing_cache", "missing_sources"])
def test_dry_run_does_not_run_tools_or_write_output(project, monkeypatch, state):
    """Planning must not install dependencies, invoke colcon, or create files."""
    if state != "ready":
        require_bootstrap(missing_sources=state == "missing_sources")
    monkeypatch.setenv("PREINSTALL_UID", "1001")
    before = rosdep_files()
    result = invoke(project, "--dry-run")
    assert result.returncode == 0, result.stderr
    assert calls() == []
    assert not (project / "pre_install").exists()
    assert "rosdep install" in result.stdout
    assert "colcon --log-base" in result.stdout
    assert rosdep_files() == before
    assert ("rosdep init" in result.stdout) == (state == "missing_sources")
    assert ("rosdep update --rosdistro jazzy" in result.stdout) == (state != "ready")


@pytest.mark.parametrize(
    "tool, code, verbs",
    [
        ("ROSDEP_INIT", 11, ["init"]),
        ("ROSDEP_UPDATE", 13, ["init", "update"]),
        ("ROSDEP_INSTALL", 17, ["init", "update", "install"]),
        ("COLCON", 23, ["init", "update", "install"]),
    ],
)
def test_failure_propagates_without_claiming_success(
    project, monkeypatch, tool, code, verbs
):
    """Each failing phase stops the chain without printing unexecuted build plans."""
    require_bootstrap(missing_sources=True)
    monkeypatch.setenv(f"PREINSTALL_{tool}_EXIT", str(code))
    result = invoke(project)
    assert result.returncode == code
    assert "Source the Unitree underlay" not in result.stdout
    recorded = calls()
    assert [arguments[0] for name, arguments in recorded if name == "rosdep"] == verbs
    assert [name for name, _ in recorded] == ["rosdep"] * len(verbs) + (
        ["colcon"] if tool == "COLCON" else []
    )
    assert ("colcon --log-base" in result.stdout) == (tool == "COLCON")
    assert "install -D" not in result.stdout


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
