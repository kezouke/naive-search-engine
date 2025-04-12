#!/bin/bash

echo "===== Running Search ====="

source /app/.venv/bin/activate

export PYSPARK_DRIVER_PYTHON=$(which python)
export PYSPARK_PYTHON=./.venv/bin/python

QUERY="$1"

unset PYSPARK_DRIVER_PYTHON

spark-submit --master yarn \
  --deploy-mode client \
  --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./.venv/bin/python \
  --conf spark.jars.exclude=kubernetes-*.jar \
  --conf spark.executor.extraClassPath="/apps/spark/jars/*" \
  --conf spark.driver.extraClassPath="/apps/spark/jars/*" \
  --archives /app/.venv.tar.gz#.venv \
  --packages com.datastax.spark:spark-cassandra-connector_2.12:3.5.0,com.github.jnr:jnr-posix:3.1.15 \
  --repositories https://jitpack.io \
  query.py "$QUERY"

echo "Done searching!"
