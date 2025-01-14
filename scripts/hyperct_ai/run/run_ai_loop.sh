#!/bin/bash
source /home/gxt/miniconda3/bin/activate /home/gxt/miniconda3/envs/image

search_dir=/home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run

jobIDs=()
for recfile in "$search_dir"/rec*
do
    rec_jobID=$(sbatch --parsable $recfile)
    echo "recon job id is $rec_jobID"
    jobIDs+=("$rec_jobID")
done

eva_jobID=$(sbatch --parsable --dependency=afterok:$(echo ${jobIDs[*]} | tr ' ' ,) /home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/eva.sh)
echo "Evaluate job id is $eva_jobID"

sbatch --dependency=afterok:${eva_jobID} /home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/ang_prop.sh

