#!/bin/bash
echo "Last time running cron_job_script_full_loop: " >> /SNS/VENUS/IPTS-33531/shared/ai_output/logs/cron_jobs.txt
date >> /SNS/VENUS/IPTS-33531/shared/ai_output/logs/cron_jobs.txt
source /opt/anaconda/etc/profile.d/conda.sh
conda activate ImagingReduction
python /SNS/VENUS/IPTS-33531/shared/hype_ipts_33531/scripts/run_full_processing_ai_loop.py

## this cron job will be ran from hype every minute !