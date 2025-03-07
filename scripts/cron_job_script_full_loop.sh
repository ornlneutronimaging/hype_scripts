#!/bin/bash
echo "Last time running cron_job_script_full_loop: " >> /SNS/VENUS/IPTS-35790/shared/hype/logs/cron_jobs.txt
date >> /SNS/VENUS/IPTS-35790/shared/hype/logs/cron_jobs.txt
source /opt/anaconda/etc/profile.d/conda.sh
conda activate ImagingReduction
python /SNS/VENUS/IPTS-35790/shared/hype/scripts/ai_processing_loop.py

## this cron job will be ran from hype every minute !