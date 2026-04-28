#!/bin/bash

set -euo pipefail

SEARCH_DIR="${PWD}"
ACTIVITY_REPO=""
for _ in 1 2 3 4 5 6; do
  if [ -f "${SEARCH_DIR}/setup_env.sh" ] && [ -d "${SEARCH_DIR}/plate2D/static" ] && \
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
  echo "Could not find the gdsims2026_ElmerFEM root."
  return 1 2>/dev/null || exit 1
fi

source "${ACTIVITY_REPO}/setup_env.sh"
