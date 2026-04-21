#!/bin/bash
echo "Last time running cron_job_script_pre_processing.sh: " >> /SNS/VENUS/shared/software/git/hype_scripts/logs/cron_jobs.txt
date >> /SNS/VENUS/shared/software/git/hype_scripts/logs/cron_jobs.txt
# source /opt/anaconda/etc/profile.d/conda.sh
# conda activate ImagingReduction
#python /SNS/VENUS/shared/software/git/hype_scripts/scripts/ai_processing_loop.py -p
/home/j35/.pixi/bin/pixi run --manifest-path /SNS/VENUS/shared/software/git/hype_scripts python /SNS/VENUS/shared/software/git/hype_scripts/scripts/ai_processing_loop.py -p