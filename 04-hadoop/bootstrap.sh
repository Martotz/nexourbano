#!/usr/bin/env bash
# M4 · Bootstrap del sandbox Hadoop. Corre en el contenedor hadoop-edge.
#   docker compose exec -T hadoop-edge bash /nexo/04-hadoop/bootstrap.sh
set -uo pipefail
export HADOOP_HOME="${HADOOP_HOME:-/opt/hadoop}" HADOOP_CONF_DIR="${HADOOP_CONF_DIR:-/opt/hadoop/etc/hadoop}"
LOG=/nexo/evidence/hadoop/bootstrap.log
exec > >(tee "$LOG") 2>&1
run() { echo; echo "\$ $*"; "$@"; }

echo "# Bootstrap Hadoop NexoUrbano — $(date -u +%FT%TZ)"
echo "# Imágenes: apache/hadoop:3.3.6 (namenode, datanode, resourcemanager, nodemanager, edge)"
run hadoop version
run java -version
echo; echo "# Esperando a que el NameNode salga de safe mode..."
hdfs dfsadmin -safemode wait
run hdfs dfs -ls /
run hdfs dfsadmin -report
run yarn node -list
run pig -version
run flume-ng version
