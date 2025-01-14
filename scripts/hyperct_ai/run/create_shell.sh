#!/bin/bash
output_file=test_leile # change for output file name
wav_id=0

TMP_PTH="/home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/templates"
DES_PTH="/home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/"

tmp_pth="$TMP_PTH/rec_tmp.sh"
file_pth="$DES_PTH/rec_1.sh"

sed "s/OUTPUT_FILE/$output_file/g; s/WAVID/$wav_id/g" "$tmp_pth" > "$file_pth"

tmp_pth="$TMP_PTH/eva_tmp.sh"
file_pth="$DES_PTH/eva.sh"

sed "s/OUTPUT_FILE/$output_file/g" "$tmp_pth" > "$file_pth"

tmp_pth="$TMP_PTH/ang_prop_tmp.sh"
file_pth="$DES_PTH/ang_prop.sh"
angle_mode=preset

sed "s/OUTPUT_FILE/$output_file/g; s/ANGLE_MODE/$angle_mode/g" "$tmp_pth" > "$file_pth"
