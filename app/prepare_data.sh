#!/bin/bash

# Activate your venv (already created in app.sh)
source .venv/bin/activate

# Make sure PySpark driver uses the current Python
export PYSPARK_DRIVER_PYTHON=$(which python)

# Unset PYSPARK_PYTHON so executors default to system python or the venv you have
unset PYSPARK_PYTHON

# 1) Copy the parquet file from local container filesystem to HDFS at /a.parquet
hdfs dfs -put -f a.parquet /

# Create parent directory for index if it doesn't exist
hdfs dfs -mkdir -p /index

# 2) Run the PySpark script that:
#    - Reads from /a.parquet
#    - Creates local "data/*.txt" files
#    - Writes single-partition TSV to /index/data
spark-submit \
  --driver-memory 6g \
  --executor-memory 6g \
  --conf "spark.executor.extraJavaOptions=-XX:MaxDirectMemorySize=512M" \
  prepare_data.py

# 3) Now put the local "data" folder to HDFS /data
echo "Putting local data/*.txt files to HDFS /data ..."
hdfs dfs -put -f data /    # now each .txt file is in HDFS /data

# 4) Check what got uploaded
echo "HDFS /data listing:"
hdfs dfs -ls /data

echo "HDFS /index/data listing:"
hdfs dfs -ls /index/data

echo "Done data preparation!"
