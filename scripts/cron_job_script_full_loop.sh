#!/bin/bash
echo "Last time running cron_job_script_full_loop: " >> /SNS/VENUS/shared/software/git/hype_scripts/logs/cron_jobs.txt
date >> /SNS/VENUS/shared/software/git/hype_scripts/logs/cron_jobs.txt
source /opt/anaconda/etc/profile.d/conda.sh
conda activate ImagingReduction
python /SNS/VENUS/shared/software/git/hype_scripts/scripts/ai_processing_loop.py

## this cron job will be ran from hype every minute !