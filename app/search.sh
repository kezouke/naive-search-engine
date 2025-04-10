#!/bin/bash

echo "===== Running Search ====="

source /app/.venv/bin/activate

export PYSPARK_DRIVER_PYTHON=$(which python)
export PYSPARK_PYTHON=/app/.venv/bin/python

QUERY="$1"

unset PYSPARK_DRIVER_PYTHON

spark-submit --master yarn \
  --deploy-mode cluster \
  --packages com.datastax.spark:spark-cassandra-connector_2.12:3.5.0 \
  --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=/app/.venv/bin/python \
  --conf spark.dynamicAllocation.enabled=true \
  --conf spark.dynamicAllocation.minExecutors=1 \
  --conf spark.dynamicAllocation.maxExecutors=4 \
  --archives /app/.venv.tar.gz#.venv \
  /app/query.py "$QUERY"

echo "Done searching!"