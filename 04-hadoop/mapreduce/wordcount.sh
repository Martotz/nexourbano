#!/usr/bin/env bash
# M5 · WordCount (MapReduce sobre YARN) de tickets de soporte + menciones sociales. Corre en hadoop-edge.
#   docker compose exec -T hadoop-edge bash /nexo/04-hadoop/mapreduce/wordcount.sh
set -euo pipefail
LOG=/nexo/evidence/hadoop/wordcount.log
OUT_LOCAL=/nexo/04-hadoop/mapreduce/output
exec > >(tee "$LOG") 2>&1
run() { echo; echo "\$ $*"; "$@"; }

echo "# WordCount NexoUrbano — $(date -u +%FT%TZ)"
hdfs dfs -rm -r -f -skipTrash /nexo/bronze/ops_texto /nexo/gold/wordcount >/dev/null 2>&1 || true
run hdfs dfs -mkdir -p /nexo/bronze/ops_texto
run hdfs dfs -put -f /nexo/data/texto_ops.txt /nexo/bronze/ops_texto/
if [ -s /nexo/data/menciones_social.txt ]; then
  run hdfs dfs -put -f /nexo/data/menciones_social.txt /nexo/bronze/ops_texto/
else
  echo "# (sin data/menciones_social.txt: correr primero la ingesta M3 para sumar menciones sociales)"
fi
run hdfs dfs -ls /nexo/bronze/ops_texto

JAR=$(ls "$HADOOP_HOME"/share/hadoop/mapreduce/hadoop-mapreduce-examples-*.jar | head -1)
run hadoop jar "$JAR" wordcount /nexo/bronze/ops_texto /nexo/gold/wordcount
run hdfs dfs -ls /nexo/gold/wordcount

mkdir -p "$OUT_LOCAL"
hdfs dfs -cat /nexo/gold/wordcount/part-r-00000 > "$OUT_LOCAL/part-r-00000"
echo; echo "# part-r-00000 copiado a 04-hadoop/mapreduce/output/ ($(wc -l < "$OUT_LOCAL/part-r-00000") términos distintos)"

# Top 20 términos operativos: minúsculas, sin IDs (V0001, ST003, R0042) ni palabras vacías.
STOP=" la el los las en de del al a y o no un una que se por con para es su sus lo le mi me ya muy mas más hay the to and of in is it for on rt "
awk -v stop="$STOP" '{
    w=tolower($1); gsub(/^[#@]/,"",w); gsub(/[^a-z0-9_áéíóúñ]/,"",w);
    if (w=="" || length(w)<3 || w ~ /^(v|st|r)[0-9]+$/ || w ~ /^[0-9]+$/ || index(stop," " w " ")) next;
    c[w]+=$2
  } END { for (w in c) print c[w] "\t" w }' "$OUT_LOCAL/part-r-00000" | sort -k1,1nr | head -20 \
  | awk 'BEGIN{print "rank\tconteo\ttermino"} {print NR "\t" $1 "\t" $2}' > /nexo/04-hadoop/mapreduce/top20_terminos.tsv
echo; echo "# Top 20 términos operativos"
cat /nexo/04-hadoop/mapreduce/top20_terminos.tsv
