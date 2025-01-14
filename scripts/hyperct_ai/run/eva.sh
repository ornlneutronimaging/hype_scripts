#!/bin/bash

#SBATCH --job-name=evaluate
#SBATCH --nodes=1 --exclusive
#SBATCH --mem=16G
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h100:1
#SBATCH --tmp=50G
#SBATCH --time=00:30:00
#SBATCH --output=/home/gxt/Projects/outputs/ceshi_ouput.txt
#SBATCH --open-mode=append
#SBATCH --error=/home/gxt/Projects/outputs/ceshi_error.err


echo "Job start at $(date)"
start=$(date +%s)

source /home/gxt/miniconda3/bin/activate image
python /home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/scrs/ai_loop.py --mode='evaluate'

echo "Job end at $(date)"
end=$(date +%s)

echo Execution time was $((end-start)) seconds. 
#>> /home/gxt/Projects/hype_node_test/outputs/gnode_run_time.txt