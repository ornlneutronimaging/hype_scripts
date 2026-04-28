#!/bin/bash
set -euo pipefail

SHARED_ROOT="/data/VENUS/shared/software/hype_scripts/hype_loop/hyperct_toolkit_depoly"
ENV_PY="${SHARED_ROOT}/.pixi/envs/svmbir-gpu-jax/bin/python"
SCRIPT="${SHARED_ROOT}/hyperct_loop_autogen/exp_pre.py"

test -x "${ENV_PY}" || { echo "ERROR: shared env python not found: ${ENV_PY}"; exit 1; }
test -f "${SCRIPT}" || { echo "ERROR: script not found: ${SCRIPT}"; exit 1; }

"${ENV_PY}" "${SCRIPT}"