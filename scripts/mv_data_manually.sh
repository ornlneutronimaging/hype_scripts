#!/bin/bash

search_dir=/storage/VENUS/IPTS-33531/images/mcp/November22_2024_CrushedRing_B
#/SNS/VENUS/IPTS-33531/shared/autoreduce/mcp/November22_CrushedRing_B
#search_str=*November22_CrushedRing_B_hyperCT_60Hz_1_8Angsmin*

dist_dir=/storage/VENUS/IPTS-33531/images/mcp
#$search_dir/$search_str


for i in $(seq 7 3 50);
do
  echo $i
  for eachfolder in $(ls -1 "$search_dir" | sort -t'_' -n -k13 | awk 'NR>=var1 && NR<=var2' var1=$i var2=$((i+2)))
  do
    filename=$(basename "$eachfolder") #eachfolder
    echo "> Move $search_dir/$filename"
    cp -r "$search_dir/$filename" "$dist_dir/"
  done 
  ./hyperct_ai/run/run_ai_loop.sh 
  sleep 660s
done

# PID 2248575