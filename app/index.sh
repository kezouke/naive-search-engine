#!/bin/bash

echo "===== Running MapReduce Indexer ====="

source /app/.venv/bin/activate

# 1) Default input path in HDFS if not specified as an argument
INPUT_PATH=${1:-/index/data}

# 2) Temporary output paths in HDFS
TMP_OUT1=/tmp/index/out1
TMP_OUT2=/tmp/index/out2

# Cleanup any old directories
hdfs dfs -rm -r -f $TMP_OUT1
hdfs dfs -rm -r -f $TMP_OUT2

########################
# Pipeline 1: Document stats
########################
echo "---- Pipeline 1: Document Stats ----"
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -files /app/mapreduce/mapper1.py,/app/mapreduce/reducer1.py \
  -archives /app/.venv.tar.gz#.venv \
  -D mapreduce.reduce.memory.mb=2048 \
  -D mapreduce.reduce.java.opts=-Xmx1800m \
  -mapper ".venv/bin/python mapper1.py" \
  -reducer ".venv/bin/python reducer1.py" \
  -input "$INPUT_PATH" \
  -output "$TMP_OUT1" \
  -numReduceTasks 1 2>&1 | tee mr_job1.log

########################
# Pipeline 2: Term aggregator
########################
echo "---- Pipeline 2: Term Aggregator ----"
hadoop jar $HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -files /app/mapreduce/mapper2.py,/app/mapreduce/reducer2.py \
    -archives /app/.venv.tar.gz#.venv \
    -D mapreduce.reduce.memory.mb=2048 \
    -D mapreduce.reduce.java.opts=-Xmx1800m \
    -mapper ".venv/bin/python mapper2.py" \
    -reducer ".venv/bin/python reducer2.py" \
    -input "$INPUT_PATH" \
    -output "$TMP_OUT2" \
    -numReduceTasks 1 2>&1 | tee mr_job2.log

echo "Indexing complete!"
