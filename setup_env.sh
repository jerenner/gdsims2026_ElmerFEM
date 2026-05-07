#!/bin/bash

# This file is meant to be sourced by an interactive shell. Do not use
# "set -e" or "set -u" here because those options would remain active after the
# script finishes and could make the student's terminal exit unexpectedly.

GARFIELD_DEFAULT_ROOT="${GARFIELD_ROOT:-/home/student/Software/garfield/garfield-20260325}"
GARFIELD_DEFAULT_SETUP="${GARFIELD_DEFAULT_ROOT}/build/setupGarfield.sh"

echo "Checking gdsims2026_ElmerFEM environment..."

missing_tools=0
for tool in ElmerGrid ElmerSolver gmsh cmake python3; do
  if command -v "${tool}" >/dev/null 2>&1; then
    echo "  [OK] ${tool}: $(command -v "${tool}")"
  else
    echo "  [ERROR] ${tool} was not found in PATH."
    missing_tools=1
  fi
done

if command -v python3 >/dev/null 2>&1; then
  if python3 -c "import matplotlib" >/dev/null 2>&1; then
    echo "  [OK] python3 matplotlib"
  else
    echo "  [ERROR] python3 matplotlib was not found."
    echo "          Install it with: sudo apt install python3-matplotlib"
    missing_tools=1
  fi
fi

if [ -z "${GARFIELD_INSTALL:-}" ] && [ -f "${GARFIELD_DEFAULT_SETUP}" ]; then
  # The student VM should normally source this from ~/.bashrc already. This
  # fallback keeps new terminals or non-interactive shells from being surprising.
  source "${GARFIELD_DEFAULT_SETUP}"
  echo "  [OK] Sourced Garfield++ setup: ${GARFIELD_DEFAULT_SETUP}"
fi

if [ -n "${GARFIELD_INSTALL:-}" ]; then
  echo "  [OK] GARFIELD_INSTALL=${GARFIELD_INSTALL}"
elif [ -n "${Garfield_DIR:-}" ]; then
  if [ -f "${Garfield_DIR}/GarfieldConfig.cmake" ]; then
    export Garfield_DIR
    echo "  [OK] Garfield_DIR=${Garfield_DIR}"
  else
    echo "  [ERROR] Garfield_DIR is set, but GarfieldConfig.cmake was not found there."
    missing_tools=1
  fi
else
  echo "  [ERROR] Neither GARFIELD_INSTALL nor Garfield_DIR is set."
  echo "          Expected ~/.bashrc to source ${GARFIELD_DEFAULT_SETUP}"
  missing_tools=1
fi

if [ -n "${Garfield_DIR:-}" ]; then
  echo "  [OK] CMake can use Garfield_DIR"
elif [ -n "${CMAKE_PREFIX_PATH:-}" ]; then
  case ":${CMAKE_PREFIX_PATH}:" in
    *":${GARFIELD_INSTALL:-__missing__}:"*)
      echo "  [OK] CMAKE_PREFIX_PATH includes Garfield++"
      ;;
    *)
      echo "  [WARNING] CMAKE_PREFIX_PATH is set, but it may not include Garfield++."
      echo "            If CMake cannot find Garfield, source ${GARFIELD_DEFAULT_SETUP}"
      ;;
  esac
else
  echo "  [WARNING] CMAKE_PREFIX_PATH is empty."
  echo "            If CMake cannot find Garfield, source ${GARFIELD_DEFAULT_SETUP}"
fi

if [ "${missing_tools}" -ne 0 ]; then
  echo "Environment check failed. Please fix the missing item(s) above."
  return 1 2>/dev/null || exit 1
fi

echo "Environment check complete."
