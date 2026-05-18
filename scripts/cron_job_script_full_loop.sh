#!/bin/bash
echo "Last time running cron_job_script_full_loop: " >> /SNS/VENUS/shared/software/git/hype_scripts/logs/cron_jobs.txt
date >> /SNS/VENUS/shared/software/git/hype_scripts/logs/cron_jobs.txt
/home/j35/.pixi/bin/pixi run --manifest-path /SNS/VENUS/shared/software/git/hype_scripts python /SNS/VENUS/shared/software/git/hype_scripts/scripts/ai_processing_loop.py
