#!/bin/bash

# Activity-local convenience wrapper. The real checks live at the repository
# root so both activities use the same environment assumptions.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../setup_env.sh"
