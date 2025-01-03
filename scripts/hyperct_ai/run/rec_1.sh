#!/bin/bash

#SBATCH --job-name=recon1
#SBATCH --nodes=2 --exclusive
#SBATCH --mem=64G 
#SBATCH --partition=cpu
#SBATCH --tmp=50G
#SBATCH --output=/home/gxt/Projects/outputs/test_new.txt
#SBATCH --open-mode=append
#SBATCH --error=/home/gxt/Projects/error/%x_%j.err

echo "Job start at $(date)" 
start=$(date +%s)

source /home/gxt/miniconda3/bin/activate /home/gxt/miniconda3/envs/image
python /home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/scrs/ai_loop.py --mode='recon' --wav_idx=0 

echo "Job end at $(date)" 
end=$(date +%s)

echo Execution time was $((end-start)) seconds. 

time sleep 20s # make sure the data saving completed
echo 'waiting time done'
#echo Delet recon for next test
#rm /storage/gxt/ai_loop_large_recon_output/CT_GS_loopCronTest_10C/Recons/wav_270_480/Ang_num_027.tiff