#!/bin/bash

# Base folder containing generated job scripts (load_*, rec_*, eva.sh, ang_prop.sh)
search_dir=/data/VENUS/shared/software/hype_scripts/hype_loop/run

shopt -s nullglob

# Submit load jobs and remember their IDs by band index
declare -A load_map
echo "Submitting load jobs (if any)..."
for loadfile in "$search_dir"/load_*; do
    idx=${loadfile##*/load_}
    idx=${idx%.sh}
    load_jobID=$(sbatch --parsable "$loadfile")
    echo "load job id is $load_jobID ($loadfile)"
    load_map[$idx]=$load_jobID
done

# Submit recon jobs; each recon depends on its matching load (if present)
rec_ids=()
echo "Submitting recon jobs..."
for recfile in "$search_dir"/rec_*; do
    idx=${recfile##*/rec_}
    idx=${idx%.sh}
    dep=""
    if [[ -n "${load_map[$idx]}" ]]; then
        dep="--dependency=afterok:${load_map[$idx]}"
    fi
    rec_jobID=$(sbatch --parsable $dep "$recfile")
    echo "recon job id is $rec_jobID ($recfile) depends on load $idx: ${load_map[$idx]}"
    rec_ids+=("$rec_jobID")
done

if [ ${#rec_ids[@]} -eq 0 ]; then
    echo "No recon jobs submitted; skipping evaluate/angle."
    exit 0
fi

dep_rec=$(echo ${rec_ids[*]} | tr ' ' ,)
eva_jobID=$(sbatch --parsable --dependency=afterok:${dep_rec} "$search_dir"/eva.sh)
echo "Evaluate job id is $eva_jobID"

ang_jobID=$(sbatch --parsable --dependency=afterok:${eva_jobID} "$search_dir"/ang_prop.sh)
echo "Angle proposal job id is $ang_jobID"

echo "Waiting for angle job ${ang_jobID} to finish on compute node..."

FLAG_FILE="/data/VENUS/shared/software/hype_scripts/logs/angle_${ang_jobID}.done"
rm -f "${FLAG_FILE}"

flag_jobID=$(sbatch --parsable \
  --partition=cpu \
  --dependency=afterok:${ang_jobID} \
  --wrap="touch ${FLAG_FILE}")
echo "Flag job id is $flag_jobID"

echo "Waiting for angle completion flag..."
while [[ ! -f "${FLAG_FILE}" ]]; do
    sleep 30
done

echo "Running sync_data.py on main node..."
/data/VENUS/shared/software/hype_scripts/hype_loop/hyperct_toolkit_depoly/.pixi/envs/svmbir-jax/bin/python \
    /data/VENUS/shared/software/hype_scripts/hype_loop/scrs/sync_data.py