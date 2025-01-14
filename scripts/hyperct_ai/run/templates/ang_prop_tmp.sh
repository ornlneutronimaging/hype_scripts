#!/bin/bash

#SBATCH --job-name=ang_prop
#SBATCH --nodes=2 --exclusive
#SBATCH --mem=64G 
#SBATCH --partition=cpu
#SBATCH --tmp=50G
#SBATCH --output=LOG_PTH/PREFIX_output.txt
#SBATCH --open-mode=append
#SBATCH --error=LOG_PTH/PREFIX_error.err

echo "Job start at $(date)"
start=$(date +%s)

source /home/gxt/miniconda3/bin/activate image
python /home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/scrs/ai_loop.py --mode='angle' --angle_mode='ANGLE_MODE'

echo "Job end at $(date)"
end=$(date +%s)

echo Execution time was $((end-start)) seconds. 

#>> /home/gxt/Projects/hype_node_test/outputs/gnode_run_time.txt