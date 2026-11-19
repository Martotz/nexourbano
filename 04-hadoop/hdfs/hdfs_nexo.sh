#!/usr/bin/env bash
# M5 · Práctica HDFS sobre datos de NexoUrbano. Corre en hadoop-edge.
#   docker compose exec -T hadoop-edge bash /nexo/04-hadoop/hdfs/hdfs_nexo.sh
set -euo pipefail
LOG=/nexo/evidence/hadoop/hdfs_nexo.log
exec > >(tee "$LOG") 2>&1
run() { echo; echo "\$ $*"; "$@"; }

echo "# HDFS NexoUrbano — $(date -u +%FT%TZ)"
hdfs dfs -rm -r -f -skipTrash /nexo >/dev/null 2>&1 || true   # idempotente: se puede correr de nuevo

run hdfs dfs -mkdir -p /nexo/bronze/viajes /nexo/bronze/viajes_full /nexo/bronze/logs /nexo/silver /nexo/gold
run hdfs dfs -put -f /nexo/data/viajes_muestra.csv /nexo/bronze/viajes/
run hdfs dfs -put -f /nexo/data/viajes.csv /nexo/bronze/viajes_full/
run hdfs dfs -ls -R /nexo
run hdfs dfs -mkdir -p /nexo/bronze/viajes/backup
run hdfs dfs -cp /nexo/bronze/viajes/viajes_muestra.csv /nexo/bronze/viajes/backup/
run hdfs dfs -mv /nexo/bronze/viajes/backup/viajes_muestra.csv "/nexo/bronze/viajes/backup/viajes_muestra_$(date +%Y%m%d).csv"
run hdfs dfs -ls -R /nexo/bronze/viajes
run hdfs dfs -du -h /nexo
run hdfs dfs -du -s -h /nexo/bronze

echo; echo "# Bloques y replicación del archivo grande (160 MB > 128 MB => 2 bloques)"
run hdfs getconf -confKey dfs.blocksize
run hdfs getconf -confKey dfs.replication
run hdfs dfs -stat "bloque=%o B  replicacion=%r  tamano=%b B  %n" /nexo/bronze/viajes_full/viajes.csv
run hdfs fsck /nexo/bronze/viajes_full/viajes.csv -files -blocks -locations

cat <<'TXT'

# ---------------------------------------------------------------------------
# Comentario del squad (8 líneas)
# 1. Tamaño de bloque: 128 MB (dfs.blocksize=134217728, default de Hadoop 3).
# 2. viajes.csv (1 M filas, ~160 MB) queda en 2 bloques: uno de 128 MB y otro con el resto; fsck lo muestra.
# 3. Factor de replicación: 1, porque el sandbox tiene un solo DataNode (en producción, 3).
# 4. El NameNode guarda solo metadatos (qué bloques forman cada archivo y dónde están); los datos están en el DataNode.
# 5. Si muere 1 DataNode con replicación 1, los bloques que tenía quedan "missing" y el archivo no se puede leer
#    (fsck pasa a CORRUPT) hasta que el nodo vuelva: no hay otra copia.
# 6. Con replicación 3 y varios DataNodes, el NameNode deja de recibir heartbeats (~10 min), marca el nodo como
#    muerto y re-replica sus bloques desde las copias sanas a otros nodos hasta volver a 3. Los clientes leen
#    de otra réplica sin enterarse.
# ---------------------------------------------------------------------------
TXT
