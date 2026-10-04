"""Build the bundled Unitree underlay and consume its actual installed types."""

import os
import subprocess
import tempfile
from pathlib import Path


def run_logged(command, cwd, log, *, env=None):
    """Keep build evidence in the designated artifact directory on failure too."""
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
            timeout=240,
            check=False,
        )
    assert result.returncode == 0, (
        f"Command failed ({result.returncode}); see {log}\n"
        f"{log.read_text(encoding='utf-8')[-6000:]}"
    )


def test_real_pre_install_is_reusable_from_an_unrelated_directory():
    """Verify installation, a repeat invocation and both Python/C++ consumers."""
    source = Path(os.environ["RV2_PROJECT_SOURCE_DIR"]).resolve()
    artifact_parent = Path(os.environ["RV2_UNITREE_TEST_OUTPUT_DIR"]).resolve()
    artifact_parent.mkdir(parents=True, exist_ok=True)
    artifacts = Path(tempfile.mkdtemp(prefix="real preinstall ", dir=artifact_parent))
    # Docker runs as root; keep retained logs readable from the host workspace.
    artifacts.chmod(0o755)
    caller = artifacts / "unrelated caller"
    caller.mkdir()
    output = artifacts / "underlay with spaces"
    script = source / "pre_install.sh"
    command = [str(script), "--output-dir", str(output)]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    run_logged(command, caller, artifacts / "first-preinstall.log", env=environment)
    install = output / "install"
    assert (install / "setup.bash").is_file()
    assert (output / "build").is_dir()
    assert (output / "log").is_dir()

    packages = ("unitree_api", "unitree_go", "unitree_hg")
    vendor = source / "ros2_ws/src/rv2_server_control/thirdparty/unitree"
    license_text = (vendor / "LICENSE").read_bytes()
    for package in packages:
        assert (install / "share" / package / "LICENSE").read_bytes() == license_text

    preserved = install / ".pre-install-preserved-marker"
    preserved.write_text("keep the existing installation\n", encoding="utf-8")
    run_logged(command, caller, artifacts / "second-preinstall.log", env=environment)
    assert preserved.read_text(encoding="utf-8") == "keep the existing installation\n"

    # A fresh shell must discover this underlay, not silently use an inherited
    # workspace's Unitree installation or Python module search path.
    fresh_environment = environment.copy()
    for name in (
        "AMENT_PREFIX_PATH",
        "CMAKE_PREFIX_PATH",
        "COLCON_PREFIX_PATH",
        "LD_LIBRARY_PATH",
        "PYTHONPATH",
        "ROS_PACKAGE_PATH",
    ):
        fresh_environment.pop(name, None)
    python_check = """
import importlib
import sys
from pathlib import Path

from ament_index_python.packages import get_package_prefix
from rclpy.serialization import deserialize_message, serialize_message
from unitree_api.msg import Request
from unitree_go.msg import LowCmd as GoLowCmd
from unitree_hg.msg import LowCmd as HgLowCmd

install = Path(sys.argv[1]).resolve()
for name in ("unitree_api", "unitree_go", "unitree_hg"):
    assert Path(get_package_prefix(name)).resolve() == install, name
    module = importlib.import_module(name + ".msg")
    assert Path(module.__file__).resolve().is_relative_to(install), module.__file__

request = Request()
request.header.identity.api_id = 1008
request.parameter = '{"x":0.25,"y":0.0,"z":0.0}'
go = GoLowCmd()
hg = HgLowCmd()
assert len(go.motor_cmd) == 20
assert len(hg.motor_cmd) == 35
go.motor_cmd[0].q = 0.5
hg.motor_cmd[0].q = -0.5
for message in (request, go, hg):
    restored = deserialize_message(serialize_message(message), type(message))
    assert restored == message, type(message)
print("All three installed Unitree packages discovered and serialized successfully")
"""
    run_logged(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-c",
            'set -eo pipefail; source "$1/setup.bash"; exec python3 -c "$2" "$1"',
            "unitree-python-consumer",
            str(install),
            python_check,
        ],
        caller,
        artifacts / "python-consumer.log",
        env=fresh_environment,
    )

    consumer = artifacts / "downstream consumer"
    consumer.mkdir()
    (consumer / "CMakeLists.txt").write_text(
        """cmake_minimum_required(VERSION 3.16)
project(unitree_preinstall_consumer LANGUAGES CXX)
find_package(ament_cmake REQUIRED)
foreach(package unitree_api unitree_go unitree_hg)
  find_package(${package} REQUIRED)
  if(NOT "${${package}_DIR}" STREQUAL
      "${UNITREE_EXPECTED_INSTALL}/share/${package}/cmake")
    message(FATAL_ERROR "${package} was not found in the new underlay")
  endif()
endforeach()
add_executable(unitree_consumer main.cpp)
target_compile_features(unitree_consumer PRIVATE cxx_std_17)
ament_target_dependencies(unitree_consumer unitree_api unitree_go unitree_hg)
""",
        encoding="utf-8",
    )
    (consumer / "main.cpp").write_text(
        """#include <unitree_api/msg/request.hpp>
#include <unitree_go/msg/low_cmd.hpp>
#include <unitree_hg/msg/low_cmd.hpp>
#include <rosidl_typesupport_cpp/message_type_support.hpp>

int main()
{
    unitree_api::msg::Request request;
    unitree_go::msg::LowCmd go;
    unitree_hg::msg::LowCmd hg;
    request.header.identity.api_id = 1008;
    go.motor_cmd[0].q = 0.5F;
    hg.motor_cmd[0].q = -0.5F;
    const auto* api_support = rosidl_typesupport_cpp::get_message_type_support_handle<
        unitree_api::msg::Request>();
    const auto* go_support = rosidl_typesupport_cpp::get_message_type_support_handle<
        unitree_go::msg::LowCmd>();
    const auto* hg_support = rosidl_typesupport_cpp::get_message_type_support_handle<
        unitree_hg::msg::LowCmd>();
    return request.header.identity.api_id == 1008 && go.motor_cmd[0].q == 0.5F &&
        hg.motor_cmd[0].q == -0.5F && api_support && go_support && hg_support ? 0 : 1;
}
""",
        encoding="utf-8",
    )
    run_logged(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-c",
            'set -eo pipefail; source "$1/setup.bash"; '
            'cmake -S "$2" -B "$2/build" "-DUNITREE_EXPECTED_INSTALL=$1"; '
            'cmake --build "$2/build" --parallel 2; '
            'exec "$2/build/unitree_consumer"',
            "unitree-cmake-consumer",
            str(install),
            str(consumer),
        ],
        caller,
        artifacts / "cpp-consumer.log",
        env=fresh_environment,
    )
    assert (consumer / "build/unitree_consumer").is_file()
