#!/bin/bash
# This will run only by the master node

#chown root:root /usr/local/hadoop/bin/container-executor
#chmod 6050 /usr/local/hadoop/bin/container-executor
#chown root:root /usr/local/hadoop/etc/hadoop/container-executor.cfg || true
#chmod 400 /usr/local/hadoop/etc/hadoop/container-executor.cfg || true

# Start HDFS daemons
$HADOOP_HOME/sbin/start-dfs.sh

# Start YARN daemons
$HADOOP_HOME/sbin/start-yarn.sh
yarn --daemon start resourcemanager

# Start mapreduce history server
mapred --daemon start historyserver


# track process IDs of services
jps -lm

# subtool to perform administrator functions on HDFS
# outputs a brief report on the overall HDFS filesystem
hdfs dfsadmin -report

# If namenode in safemode then leave it
hdfs dfsadmin -safemode leave

# create a directory for spark apps in HDFS
hdfs dfs -mkdir -p /apps/spark/jars
hdfs dfs -chmod 744 /apps/spark/jars


# Copy all jars to HDFS
hdfs dfs -put /usr/local/spark/jars/* /apps/spark/jars/
hdfs dfs -chmod +rx /apps/spark/jars/


# print version of Scala of Spark
scala -version

# track process IDs of services
jps -lm

# Create a directory for root user on HDFS
hdfs dfs -mkdir -p /user/root

export HADOOP_CONF_DIR=/usr/local/hadoop/etc/hadoop
export YARN_CONF_DIR=/usr/local/hadoop/etc/hadoop
echo $HADOOP_CONF_DIR
echo $YARN_CONF_DIR
