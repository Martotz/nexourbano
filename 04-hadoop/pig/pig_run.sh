#!/usr/bin/env bash
# M7 · Ejecuta clean_viajes.pig sobre HDFS (MapReduce en YARN). Corre en hadoop-edge.
#   docker compose exec -T hadoop-edge bash /nexo/04-hadoop/pig/pig_run.sh
set -uo pipefail
export HADOOP_HOME="${HADOOP_HOME:-/opt/hadoop}" HADOOP_CONF_DIR="${HADOOP_CONF_DIR:-/opt/hadoop/etc/hadoop}"
LOG=/nexo/evidence/hadoop/pig.log
exec > >(tee "$LOG") 2>&1
run() { echo; echo "\$ $*"; "$@"; }
echo "# Pig NexoUrbano — $(date -u +%FT%TZ)"
hdfs dfs -rm -r -f -skipTrash /nexo/silver/clean_viajes >/dev/null 2>&1 || true
cd /tmp
if ! run pig -x mapreduce -param INPUT=/nexo/bronze/viajes_full -param OUTPUT=/nexo/silver/clean_viajes /nexo/04-hadoop/pig/clean_viajes.pig; then
  echo "# Modo mapreduce falló: plan B, Pig en modo local sobre el CSV del repo"
  rm -rf /tmp/clean_viajes
  run pig -x local -param INPUT=/nexo/data/viajes.csv -param OUTPUT=/tmp/clean_viajes /nexo/04-hadoop/pig/clean_viajes.pig
  run hdfs dfs -mkdir -p /nexo/silver/clean_viajes
  run hdfs dfs -put -f /tmp/clean_viajes/part-* /nexo/silver/clean_viajes/
fi
run hdfs dfs -ls /nexo/silver/clean_viajes
echo; echo "# Primeras filas de la salida"
hdfs dfs -cat /nexo/silver/clean_viajes/part-* 2>/dev/null | head -5
