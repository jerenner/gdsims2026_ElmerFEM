#!/bin/bash

set -euo pipefail

SEARCH_DIR="${PWD}"
ACTIVITY_REPO=""
for _ in 1 2 3 4 5 6 7; do
  if [ -f "${SEARCH_DIR}/README.md" ] && [ -d "${SEARCH_DIR}/plate2D/static" ] && \
     [ -d "${SEARCH_DIR}/plate2D/dynamic" ]; then
    ACTIVITY_REPO="${SEARCH_DIR}"
    break
  fi
  if [ "${SEARCH_DIR}" = "/" ]; then
    break
  fi
  SEARCH_DIR="$(cd "${SEARCH_DIR}/.." && pwd)"
done

if [ -z "${ACTIVITY_REPO}" ]; then
  echo "Could not infer the gdsims2026_ElmerFEM repository root."
  return 1 2>/dev/null || exit 1
fi

SOFTWARE_ROOT="$(cd "${ACTIVITY_REPO}/.." && pwd)"

echo "Setting up gdsims2026_ElmerFEM environment..."

export ELMER_BUILD="${SOFTWARE_ROOT}/elmerfem/build"
export ELMER_HOME="${ELMER_BUILD}/fem/src"
export ELMER_SOLVER_DATADIR="${ELMER_BUILD}/fem/src"
export ELMER_LIB="${ELMER_BUILD}/fem/src/modules"
export ELMER_RESOURCES="${ELMER_BUILD}/fem/src"
export PATH="${ELMER_BUILD}/fem/src:${ELMER_BUILD}/elmergrid/src:${SOFTWARE_ROOT}/gmsh/build:${PATH}"
export DYLD_LIBRARY_PATH="${ELMER_BUILD}/fem/src:${ELMER_BUILD}/fem/src/modules:${DYLD_LIBRARY_PATH:-}"
echo "  [OK] Elmer and Gmsh"

export GARFIELD_INSTALL="${SOFTWARE_ROOT}/garfieldpp/install"
if [ -f "${GARFIELD_INSTALL}/share/Garfield/setupGarfield.sh" ]; then
  export CMAKE_PREFIX_PATH="${CMAKE_PREFIX_PATH:-}"
  export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"
  export PYTHONPATH="${PYTHONPATH:-}"
  source "${GARFIELD_INSTALL}/share/Garfield/setupGarfield.sh"
  export DYLD_LIBRARY_PATH="${GARFIELD_INSTALL}/lib:${DYLD_LIBRARY_PATH:-}"
  echo "  [OK] Garfield++"
else
  echo "  [ERROR] Garfield++ setup script not found at ${GARFIELD_INSTALL}"
fi

echo "Environment ready."
