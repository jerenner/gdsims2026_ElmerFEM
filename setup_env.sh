#!/bin/bash

set -euo pipefail

prepend_path_if_dir() {
  if [ -d "$1" ]; then
    case ":${PATH}:" in
      *":$1:"*) ;;
      *) export PATH="$1:${PATH}" ;;
    esac
  fi
}

prepend_var_if_dir() {
  local var_name="$1"
  local dir="$2"
  if [ -d "${dir}" ]; then
    local current_value="${!var_name:-}"
    case ":${current_value}:" in
      *":${dir}:"*) ;;
      *) export "${var_name}=${dir}${current_value:+:${current_value}}" ;;
    esac
  fi
}

find_upwards_repo_root() {
  local search_dir="$1"
  for _ in 1 2 3 4 5 6 7; do
    if [ -f "${search_dir}/README.md" ] && \
       [ -d "${search_dir}/plate2D/static" ] && \
       [ -d "${search_dir}/plate2D/dynamic" ]; then
      printf '%s\n' "${search_dir}"
      return 0
    fi
    if [ "${search_dir}" = "/" ]; then
      break
    fi
    search_dir="$(cd "${search_dir}/.." && pwd)"
  done
  return 1
}

find_garfield_config() {
  local search_root="$1"
  if [ ! -d "${search_root}" ]; then
    return 1
  fi
  find "${search_root}" -name GarfieldConfig.cmake -print -quit 2>/dev/null
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTIVITY_REPO="$(find_upwards_repo_root "${SCRIPT_DIR}" || true)"
if [ -z "${ACTIVITY_REPO}" ]; then
  ACTIVITY_REPO="$(find_upwards_repo_root "${PWD}" || true)"
fi
if [ -z "${ACTIVITY_REPO}" ]; then
  echo "Could not infer the gdsims2026_ElmerFEM repository root."
  return 1 2>/dev/null || exit 1
fi

SOFTWARE_ROOT="$(cd "${ACTIVITY_REPO}/.." && pwd)"

echo "Setting up gdsims2026_ElmerFEM environment..."
echo "  Repository: ${ACTIVITY_REPO}"

# Student VM defaults:
#   - ElmerGrid, ElmerSolver, and gmsh are expected to already be in PATH.
#   - Garfield++ is expected under /home/student by default.
#
# Tutor/developer overrides:
#   export GARFIELD_ROOT=/path/to/garfield-source-or-install-prefix
#   export GARFIELD_INSTALL=/path/to/garfield-install-prefix
#   export Garfield_DIR=/path/to/directory/containing/GarfieldConfig.cmake

# Keep the old adjacent-source checkout working for local development.
if [ -d "${SOFTWARE_ROOT}/elmerfem/build/fem/src" ]; then
  export ELMER_BUILD="${ELMER_BUILD:-${SOFTWARE_ROOT}/elmerfem/build}"
  export ELMER_HOME="${ELMER_HOME:-${ELMER_BUILD}/fem/src}"
  export ELMER_SOLVER_DATADIR="${ELMER_SOLVER_DATADIR:-${ELMER_BUILD}/fem/src}"
  export ELMER_LIB="${ELMER_LIB:-${ELMER_BUILD}/fem/src/modules}"
  export ELMER_RESOURCES="${ELMER_RESOURCES:-${ELMER_BUILD}/fem/src}"
  prepend_path_if_dir "${ELMER_BUILD}/fem/src"
  prepend_path_if_dir "${ELMER_BUILD}/elmergrid/src"
  prepend_var_if_dir LD_LIBRARY_PATH "${ELMER_BUILD}/fem/src"
  prepend_var_if_dir LD_LIBRARY_PATH "${ELMER_BUILD}/fem/src/modules"
  prepend_var_if_dir DYLD_LIBRARY_PATH "${ELMER_BUILD}/fem/src"
  prepend_var_if_dir DYLD_LIBRARY_PATH "${ELMER_BUILD}/fem/src/modules"
fi

if [ -d "${SOFTWARE_ROOT}/gmsh/build" ]; then
  prepend_path_if_dir "${SOFTWARE_ROOT}/gmsh/build"
fi

missing_tools=0
for tool in ElmerGrid ElmerSolver gmsh; do
  if command -v "${tool}" >/dev/null 2>&1; then
    echo "  [OK] ${tool}: $(command -v "${tool}")"
  else
    echo "  [ERROR] ${tool} was not found in PATH."
    missing_tools=1
  fi
done

if [ "${missing_tools}" -ne 0 ]; then
  echo "Please load/install Elmer and Gmsh before continuing."
  return 1 2>/dev/null || exit 1
fi

export GARFIELD_ROOT="${GARFIELD_ROOT:-/home/student/Software/garfield/garfield-20260325}"
if [ ! -d "${GARFIELD_ROOT}" ] && [ -d "${SOFTWARE_ROOT}/garfieldpp" ]; then
  export GARFIELD_ROOT="${SOFTWARE_ROOT}/garfieldpp"
fi

if [ -z "${GARFIELD_INSTALL:-}" ]; then
  if [ -f "${GARFIELD_ROOT}/share/Garfield/setupGarfield.sh" ]; then
    export GARFIELD_INSTALL="${GARFIELD_ROOT}"
  elif [ -f "${GARFIELD_ROOT}/install/share/Garfield/setupGarfield.sh" ]; then
    export GARFIELD_INSTALL="${GARFIELD_ROOT}/install"
  elif [ -f "${SOFTWARE_ROOT}/garfieldpp/install/share/Garfield/setupGarfield.sh" ]; then
    export GARFIELD_INSTALL="${SOFTWARE_ROOT}/garfieldpp/install"
  else
    export GARFIELD_INSTALL="${GARFIELD_ROOT}"
  fi
fi

export CMAKE_PREFIX_PATH="${CMAKE_PREFIX_PATH:-}"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
export PYTHONPATH="${PYTHONPATH:-}"

if [ -f "${GARFIELD_INSTALL}/share/Garfield/setupGarfield.sh" ]; then
  source "${GARFIELD_INSTALL}/share/Garfield/setupGarfield.sh"
  prepend_var_if_dir LD_LIBRARY_PATH "${GARFIELD_INSTALL}/lib"
  prepend_var_if_dir DYLD_LIBRARY_PATH "${GARFIELD_INSTALL}/lib"
  echo "  [OK] Garfield++ setup: ${GARFIELD_INSTALL}/share/Garfield/setupGarfield.sh"
else
  prepend_var_if_dir LD_LIBRARY_PATH "${GARFIELD_ROOT}/lib"
  prepend_var_if_dir LD_LIBRARY_PATH "${GARFIELD_ROOT}/build/lib"
  prepend_var_if_dir DYLD_LIBRARY_PATH "${GARFIELD_ROOT}/lib"
  prepend_var_if_dir DYLD_LIBRARY_PATH "${GARFIELD_ROOT}/build/lib"
fi

if [ -z "${Garfield_DIR:-}" ]; then
  GARFIELD_CONFIG="$(find_garfield_config "${GARFIELD_INSTALL}" || true)"
  if [ -z "${GARFIELD_CONFIG}" ]; then
    GARFIELD_CONFIG="$(find_garfield_config "${GARFIELD_ROOT}" || true)"
  fi
  if [ -n "${GARFIELD_CONFIG}" ]; then
    export Garfield_DIR="$(dirname "${GARFIELD_CONFIG}")"
  fi
fi

if [ -n "${Garfield_DIR:-}" ] && [ -f "${Garfield_DIR}/GarfieldConfig.cmake" ]; then
  prepend_var_if_dir CMAKE_PREFIX_PATH "$(cd "${Garfield_DIR}/../../.." 2>/dev/null && pwd || true)"
  echo "  [OK] Garfield++ CMake package: ${Garfield_DIR}"
else
  echo "  [ERROR] Could not find GarfieldConfig.cmake."
  echo "          Set GARFIELD_ROOT, GARFIELD_INSTALL, or Garfield_DIR and source this script again."
  return 1 2>/dev/null || exit 1
fi

echo "Environment ready."
