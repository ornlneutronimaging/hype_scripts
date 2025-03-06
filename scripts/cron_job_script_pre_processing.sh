#!/bin/bash
echo "Last time running cron_job_script_pre_processing.sh: " >> /SNS/VENUS/IPTS-35790/shared/hype/logs/cron_jobs.txt
date >> /SNS/VENUS/IPTS-35790/shared/hype/logs/cron_jobs.txt
source /opt/anaconda/etc/profile.d/conda.sh
conda activate /home/j35/.conda/envs/ImagingReduction
python /SNS/VENUS/IPTS-33531/shared/hype_ipts_33531/scripts/move_folders.py

## this cron job will be ran from hype every minute !