#!/bin/bash
echo ">>Remove old script first"
rm rec_*.sh eva.sh ang_prop.sh

log_pth=$1 #
file_prefix=$2 # change for output file name
#wav_id=0

TMP_PTH="/home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/templates"
DES_PTH="/home/gxt/Projects/hype_ipts_33531/scripts/hyperct_ai/run/"

tmp_pth="$TMP_PTH/rec_tmp.sh"

for i in ${@:4}
do
    file_pth="$DES_PTH/rec_$i.sh"
    sed "s|LOG_PTH|$log_pth|g; s/PREFIX/$file_prefix/g; s/WAVID/$(($i-1))/g" "$tmp_pth" > "$file_pth"
done

tmp_pth="$TMP_PTH/eva_tmp.sh"
file_pth="$DES_PTH/eva.sh"

sed "s|LOG_PTH|$log_pth|g; s/PREFIX/$file_prefix/g" "$tmp_pth" > "$file_pth"

tmp_pth="$TMP_PTH/ang_prop_tmp.sh"
file_pth="$DES_PTH/ang_prop.sh"
angle_mode=$3 #preset

sed "s|LOG_PTH|$log_pth|g; s/PREFIX/$file_prefix/g; s/ANGLE_MODE/$angle_mode/g" "$tmp_pth" > "$file_pth"
