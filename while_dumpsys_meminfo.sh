#!/bin/bash

source source.sh
# 格式：YYYYMMDD_HHMMSS
targetDir=dump_mem_info/"$(date +'%Y%m%d_%H%M')"
echo "dump path  ${targetDir}"
mkdir -p ${targetDir}
index=0
update_time=$(date +%s)
dump_time=$(date +%s)
dump_interval=30
update_interval=60
while true; do
  cur_time=$(date +%s)
  time_diff=$((cur_time - dump_time))
  echo "time_diff $time_diff dump_interval $dump_interval"
  if [[ $time_diff -ge $dump_interval ]]; then
      echo "dump... " `date +'%Y:%m:%d %H:%M:%S'`
      dump_time=$(date +%s)
      adb shell dumpsys meminfo > ${targetDir}/${index}.txt
      #dump_time=$(date +%s)
      index=$((index+1))
  fi

  #每隔一分钟刷新一次数据
  cur_time=$(date +%s)
  time_diff=$((cur_time - update_time))
  if [[ $time_diff -ge $update_interval ]]; then
      echo "update..."  `date +'%Y:%m:%d %H:%M:%S'`
      python3 main.py ${targetDir} 10
      update_time=$(date +%s)
  fi

  sleep 1
done
