#!/usr/bin/env bash
# Build all bundled Unitree interfaces into a separate, project-local underlay.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: pre_install.sh [--output-dir DIR] [--dry-run]

Build bundled unitree_api, unitree_go and unitree_hg after installing their ROS
dependencies with rosdep. Source your ROS 2 environment before running this file.
Missing rosdep sources/cache are initialized automatically. Initialization and
system packages may request sudo; do not run this entire script as sudo.

  --output-dir DIR  Build/install/log root (default: project/pre_install/$ROS_DISTRO).
                    Relative paths are resolved from your current directory.
  --dry-run         Print commands without installing, building or writing files.
  -h, --help        Show this help.
EOF
}

die() {
  printf 'pre_install.sh: %s\n' "$*" >&2
  exit 2
}

print_command() {
  printf '%q ' "$@"
  printf '\n'
}

run_command() {
  print_command "$@"
  if ! "$dry_run"; then
    "$@"
  fi
}

project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
output_dir=
dry_run=false
while (($#)); do
  case "$1" in
    --output-dir)
      (($# >= 2)) && [[ -n "$2" && "$2" != --* ]] || die '--output-dir requires a directory'
      output_dir=$2
      shift 2
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *) die "Unknown argument: $1" ;;
  esac
done

[[ ${ROS_VERSION:-} == 2 && ${ROS_DISTRO:-} =~ ^[a-z][a-z0-9_]*$ ]] ||
  die 'Source a ROS 2 environment first (ROS_VERSION=2 and ROS_DISTRO must be set)'
for tool in colcon rosdep python3; do
  command -v "$tool" >/dev/null || die "Required command not found: $tool"
done

output_dir=$(realpath -m -- "${output_dir:-$project_dir/pre_install/$ROS_DISTRO}")
source_tree=$project_dir/ros2_ws/src
if [[ "$output_dir" == / || "$project_dir" == "$output_dir" || "$project_dir" == "$output_dir/"* ||
  "$source_tree" == "$output_dir" || "$source_tree" == "$output_dir/"* ||
  "$output_dir" == "$source_tree/"* ]]; then
  die '--output-dir must not contain or be inside the project source tree'
fi

vendor_dir=$source_tree/rv2_server_control/thirdparty/unitree
packages=(unitree_api unitree_go unitree_hg)
package_paths=()
for package in "${packages[@]}"; do
  package_dir=$vendor_dir/$package
  [[ -f "$package_dir/package.xml" && -f "$package_dir/CMakeLists.txt" ]] ||
    die "Missing bundled package: $package_dir; initialize the project submodules first"
  package_paths+=("$package_dir")
done
[[ -f "$vendor_dir/LICENSE" ]] || die "Missing Unitree license: $vendor_dir/LICENSE"

# Use rosdep's own paths so ROS_HOME and custom source lists remain effective.
# A directory alone is not a populated cache; rosdep requires its index file.
rosdep_state=$(python3 -B - <<'PY'
from pathlib import Path

from rosdep2.sources_list import (
    CACHE_INDEX,
    get_sources_cache_dir,
    get_sources_list_dir,
    get_sources_list_dirs,
)

if (Path(get_sources_cache_dir()) / CACHE_INDEX).exists():
    print("ready")
else:
    directories = get_sources_list_dirs(get_sources_list_dir(strip_missing_dirs=False))
    if any(list(Path(directory).glob("*.list")) for directory in directories):
        print("update")
    else:
        print("init")
PY
)
if [[ "$rosdep_state" == init ]]; then
  init_command=(rosdep init)
  if [[ $(id -u) != 0 ]]; then
    command -v sudo >/dev/null || die 'rosdep initialization requires sudo; run rosdep init as root first'
    if [[ -v ROSDEP_SOURCE_PATH ]]; then
      init_command=(sudo env "ROSDEP_SOURCE_PATH=$ROSDEP_SOURCE_PATH" "${init_command[@]}")
    else
      init_command=(sudo "${init_command[@]}")
    fi
  fi
  run_command "${init_command[@]}"
fi
if [[ "$rosdep_state" != ready ]]; then
  run_command rosdep update --rosdistro "$ROS_DISTRO"
fi

rosdep_command=(
  rosdep install --from-paths "${package_paths[@]}" --ignore-src -y
  --rosdistro "$ROS_DISTRO"
  -t build -t buildtool -t build_export -t buildtool_export -t exec
)
build_command=(
  colcon --log-base "$output_dir/log" build --base-paths "${package_paths[@]}"
  --build-base "$output_dir/build" --install-base "$output_dir/install"
  --merge-install --packages-select "${packages[@]}"
  --cmake-args -DBUILD_TESTING=OFF
)

run_command "${rosdep_command[@]}"
run_command mkdir -p -- "$output_dir"
run_command touch -- "$output_dir/COLCON_IGNORE"
run_command "${build_command[@]}"
if ! "$dry_run"; then
  [[ -f "$output_dir/install/setup.bash" ]] || die 'colcon did not create install/setup.bash'
fi
for package in "${packages[@]}"; do
  run_command install -D -m 644 "$vendor_dir/LICENSE" "$output_dir/install/share/$package/LICENSE"
done
printf '\nSource the Unitree underlay in your current shell:\n'
print_command source "$output_dir/install/setup.bash"
