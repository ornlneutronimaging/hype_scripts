#!/bin/bash
source /home/gxt/miniconda3/bin/activate /home/gxt/miniconda3/envs/image

rec_jobID=$(sbatch --parsable /home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/rec_1.sh)
echo "recon job id is $rec_jobID"

eva_jobID=$(sbatch --parsable --dependency=afterok:${rec_jobID} /home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/eva.sh)
echo "Evaluate job id is $eva_jobID"

sbatch --dependency=afterok:${eva_jobID} /home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/ang_prop.sh

