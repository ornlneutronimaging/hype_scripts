#!/bin/bash

#SBATCH --job-name=evaluate
#SBATCH --nodes=1 
#SBATCH --gres=gpu:nvidia_h100_pcie:1 
#SBATCH --mem=100G
#SBATCH --partition=gpu
#SBATCH --tmp=150G
#SBATCH --output=/data/VENUS/shared/software/hype_scripts/logs/ipts_IPTS_output.txt
#SBATCH --open-mode=append
#SBATCH --error=/data/VENUS/shared/software/hype_scripts/logs/ipts_IPTS_error.err

set -euo pipefail

echo "==========Evaluation Job start at $(date)=========="
echo "Running on host: $(hostname)"
start=$(date +%s)

# Shared HyperCT deployment
SHARED_ROOT="/data/VENUS/shared/software/hype_scripts/hype_loop/hyperct_toolkit_depoly"
ENV_PY="${SHARED_ROOT}/.pixi/envs/svmbir-gpu-jax/bin/python"
AI_LOOP_SCRIPT="/data/VENUS/shared/software/hype_scripts/hype_loop/scrs/ai_loop.py"

# Auto-generated placeholder
CONFIG_PATH="CFG"

# Basic checks
test -x "${ENV_PY}" || { echo "ERROR: shared env python not found: ${ENV_PY}"; exit 1; }
test -f "${AI_LOOP_SCRIPT}" || { echo "ERROR: ai_loop script not found: ${AI_LOOP_SCRIPT}"; exit 1; }
test -f "${CONFIG_PATH}" || { echo "ERROR: config file not found: ${CONFIG_PATH}"; exit 1; }

echo "Python: ${ENV_PY}"
echo "Script: ${AI_LOOP_SCRIPT}"
echo "Config: ${CONFIG_PATH}"

"${ENV_PY}" "${AI_LOOP_SCRIPT}" \
    --cfg "${CONFIG_PATH}" \
    --mode evaluate

echo "Job end at $(date)"
end=$(date +%s)

echo "Execution time was $((end-start)) seconds."