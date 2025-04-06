#!/bin/bash
# This script takes a query string as an argument and runs query.py on YARN.

# Activate the Python virtual environment.
source .venv/bin/activate

# Set the Python executable for Spark.
export PYSPARK_DRIVER_PYTHON=$(which python)
export PYSPARK_PYTHON=./.venv/bin/python

# Check if a query was provided.
if [ "$#" -lt 1 ]; then
  echo "Usage: ./search.sh \"query string\""
  exit 1
fi

# Capture the entire query string.
QUERY="$*"

# The Spark Cassandra Connector version.
# For Spark 3.5.4 with Scala 2.12, try this connector version.
CASSANDRA_CONNECTOR="com.datastax.spark:spark-cassandra-connector_2.12:3.3.0"

spark-submit \
  --master yarn \
  --packages "$CASSANDRA_CONNECTOR" \
  --archives /app/.venv.tar.gz#.venv \
  /app/query.py "$QUERY"
