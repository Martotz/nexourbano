#!/usr/bin/env bash
# M6 · Hive: tablas, queries y demostración de DROP externa vs. interna. Corre en el contenedor hive.
#   docker compose exec -T hive bash /nexo/04-hadoop/hive/hive_run.sh
set -uo pipefail
LOG=/nexo/evidence/hadoop/hive_nexo.log
exec > >(tee "$LOG") 2>&1
NN=hdfs://namenode:8020
BL="beeline -u jdbc:hive2://localhost:10000/ -n hive --showHeader=true --outputformat=table2"
run() { echo; echo "\$ $*"; "$@"; }

echo "# Hive NexoUrbano — $(date -u +%FT%TZ)"
for i in $(seq 1 30); do $BL -e "select 1" >/dev/null 2>&1 && break; echo "esperando HiveServer2 ($i)..."; sleep 5; done

run $BL -f /nexo/04-hadoop/hive/hive_nexo.sql

echo; echo "################ DEMO DROP: externa vs. interna ################"
hdfs dfs -rm -r -f -skipTrash $NN/nexo/bronze/demo_externa >/dev/null 2>&1 || true
run hdfs dfs -mkdir -p $NN/nexo/bronze/demo_externa
run hdfs dfs -put -f /nexo/data/viajes_muestra.csv $NN/nexo/bronze/demo_externa/
run $BL -f /nexo/04-hadoop/hive/hive_drop_demo.sql

echo; echo "# ANTES del DROP: los dos directorios existen"
run hdfs dfs -ls $NN/nexo/bronze/demo_externa
run hdfs dfs -ls $NN/user/hive/warehouse/nexo.db/demo_interna

run $BL -e "USE nexo; DROP TABLE demo_externa; DROP TABLE demo_interna; SHOW TABLES;"

echo; echo "# DESPUÉS del DROP"
echo "# externa -> el CSV sigue en HDFS (Hive solo borró el esquema del metastore):"
run hdfs dfs -ls $NN/nexo/bronze/demo_externa
echo "# interna -> Hive borró el directorio del warehouse junto con los datos:"
run hdfs dfs -ls $NN/user/hive/warehouse/nexo.db/demo_interna || echo ">>> No existe: los datos de la tabla interna se perdieron con el DROP"
