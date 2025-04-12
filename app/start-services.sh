#!/bin/bash

# -----------------------------------------------------------------------------
# Hadoop & Spark Cluster Initialization Script (Master Node)
# -----------------------------------------------------------------------------

# Ensure script is executed as root if using container-executor (optional)
# chown root:root /usr/local/hadoop/bin/container-executor
# chmod 6050 /usr/local/hadoop/bin/container-executor
# chown root:root /usr/local/hadoop/etc/hadoop/container-executor.cfg || true
# chmod 400 /usr/local/hadoop/etc/hadoop/container-executor.cfg || true

# -----------------------------------------------------------------------------
# Start Hadoop Distributed File System (HDFS) and YARN daemons
# -----------------------------------------------------------------------------

echo "Starting HDFS daemons..."
$HADOOP_HOME/sbin/start-dfs.sh

echo "Starting YARN daemons..."
$HADOOP_HOME/sbin/start-yarn.sh
yarn --daemon start resourcemanager

# -----------------------------------------------------------------------------
# Start MapReduce Job History Server
# -----------------------------------------------------------------------------

echo "Starting MapReduce Job History Server..."
mapred --daemon start historyserver

# -----------------------------------------------------------------------------
# Verify running Java processes and Hadoop services
# -----------------------------------------------------------------------------

echo "Currently running Java processes (jps)..."
jps -lm

# -----------------------------------------------------------------------------
# Perform HDFS admin checks
# -----------------------------------------------------------------------------

echo "HDFS Report:"
hdfs dfsadmin -report

echo "Exiting HDFS Safe Mode (if active)..."
hdfs dfsadmin -safemode leave

# -----------------------------------------------------------------------------
# Set up Spark JARs directory in HDFS
# -----------------------------------------------------------------------------

echo "Creating directory for Spark JARs in HDFS..."
hdfs dfs -mkdir -p /apps/spark/jars
hdfs dfs -chmod 744 /apps/spark/jars

echo "Uploading local Spark JARs to HDFS..."
hdfs dfs -put /usr/local/spark/jars/* /apps/spark/jars/
hdfs dfs -chmod +rx /apps/spark/jars/

# -----------------------------------------------------------------------------
# Download and use official Spark 3.5.5 binaries (only if not already present)
# -----------------------------------------------------------------------------

SPARK_ARCHIVE="spark-3.5.5-bin-hadoop3.tgz"
SPARK_DIR="spark-3.5.5-bin-hadoop3"

if [ ! -f "$SPARK_ARCHIVE" ]; then
    echo "Downloading Spark 3.5.5..."
    wget https://archive.apache.org/dist/spark/spark-3.5.5/$SPARK_ARCHIVE
else
    echo "$SPARK_ARCHIVE already exists. Skipping download."
fi

# Extract if directory doesn't exist
if [ ! -d "$SPARK_DIR" ]; then
    echo "Extracting Spark archive..."
    tar -xzf $SPARK_ARCHIVE
else
    echo "Spark directory $SPARK_DIR already exists. Skipping extraction."
fi

echo "Replacing existing Spark JARs in HDFS with Spark 3.5.5 distribution..."
hdfs dfs -rm -r /apps/spark/jars/*
hdfs dfs -put spark-3.5.5-bin-hadoop3/jars/* /apps/spark/jars/
hdfs dfs -chmod 744 /apps/spark/jars
hdfs dfs -chmod +rx /apps/spark/jars/

# -----------------------------------------------------------------------------
# Restart HDFS and YARN daemons (to reflect any changes)
# -----------------------------------------------------------------------------

echo "Restarting HDFS and YARN daemons..."
$HADOOP_HOME/sbin/stop-dfs.sh
$HADOOP_HOME/sbin/stop-yarn.sh

$HADOOP_HOME/sbin/start-dfs.sh
$HADOOP_HOME/sbin/start-yarn.sh

# -----------------------------------------------------------------------------
# Miscellaneous setup and validation
# -----------------------------------------------------------------------------

echo "Scala version in use:"
scala -version

echo "Rechecking running Java processes..."
jps -lm

echo "Creating HDFS home directory for root user (if not already exists)..."
hdfs dfs -mkdir -p /user/root

# Export HADOOP configuration directory for use by other tools
export HADOOP_CONF_DIR=/usr/local/hadoop/etc/hadoop
echo "HADOOP_CONF_DIR set to: $HADOOP_CONF_DIR"

echo "Cluster initialization completed."