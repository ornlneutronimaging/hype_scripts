#!/bin/bash
output_file=test_haha # change for output file name
wav_id=0

tmp_pth=/home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/templates/rec_tmp.sh
file_pth=/home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/rec_1.sh

sed "s/OUTPUT_FILE/$output_file/g; s/WAVID/$wav_id/g" "$tmp_pth" > "$file_pth"

tmp_pth=/home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/templates/eva_tmp.sh
file_pth=/home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/eva.sh

sed "s/OUTPUT_FILE/$output_file/g" "$tmp_pth" > "$file_pth"

tmp_pth=/home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/templates/ang_prop_tmp.sh
file_pth=/home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/ang_prop.sh
angle_mode=preset

sed "s/OUTPUT_FILE/$output_file/g; s/ANGLE_MODE/$angle_mode/g" "$tmp_pth" > "$file_pth"