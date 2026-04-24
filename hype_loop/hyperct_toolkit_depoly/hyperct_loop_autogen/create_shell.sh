#!/bin/bash

# Usage: ./create_shell.sh <ipts_number> <num_rec_jobs>
# Example: ./create_shell.sh 35207 3
# Generates load_*.sh, rec_*.sh, eva.sh, ang_prop.sh under ${DES_PTH} with CFG_PTH injected.

ipts=$1 #
num_rec_jobs=$2 # number of reconstruction jobs
if [ -z "$2" ]; then
  echo "Error: Missing argument #2: number of reconstruction jobs, please provide a integer."
  echo "Usage: $0 <ipts> <num_rec_jobs> "
  exit 1
fi

TMP_PTH="/data/VENUS/shared/software/hype_scripts/hype_loop/hyperct_toolkit_depoly/hyperct_loop_autogen/templates"
DES_PTH='/data/VENUS/shared/software/hype_scripts/hype_loop/run'

CFG_PTH='/data/VENUS/shared/software/hype_scripts/configs/config.yaml'

echo ">>Remove old script first"
rm -f "${DES_PTH}"/load_*.sh "${DES_PTH}"/rec_*.sh "${DES_PTH}/eva.sh" "${DES_PTH}/ang_prop.sh"

tmp_pth="$TMP_PTH/load_tmp.sh"

for i in $(seq 1 $num_rec_jobs)
do
  file_pth="$DES_PTH/load_$i.sh"
  sed "s|IPTS|$ipts|g; s/RECNUM/$i/g; s/WAVID/$(($i-1))/g; s|CFG|$CFG_PTH|g" "$tmp_pth" > "$file_pth"
done

tmp_pth="$TMP_PTH/rec_tmp.sh"

for i in $(seq 1 $num_rec_jobs)
do
    file_pth="$DES_PTH/rec_$i.sh"
  sed "s|IPTS|$ipts|g; s/RECNUM/$i/g; s/WAVID/$(($i-1))/g; s|CFG|$CFG_PTH|g" "$tmp_pth" > "$file_pth"
done

tmp_pth="$TMP_PTH/eva_tmp.sh"
file_pth="$DES_PTH/eva.sh"

sed "s|IPTS|$ipts|g; s|CFG|$CFG_PTH|g" "$tmp_pth" > "$file_pth"

tmp_pth="$TMP_PTH/ang_prop_tmp.sh"
file_pth="$DES_PTH/ang_prop.sh"

sed "s|IPTS|$ipts|g; s|CFG|$CFG_PTH|g" "$tmp_pth" > "$file_pth"
