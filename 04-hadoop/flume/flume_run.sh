#!/usr/bin/env bash
# M7 · Agente Flume + simulación de 200 eventos (ride_start, ride_end, payment_fail). Corre en hadoop-edge.
#   docker compose exec -T hadoop-edge bash /nexo/04-hadoop/flume/flume_run.sh
set -uo pipefail
export HADOOP_HOME="${HADOOP_HOME:-/opt/hadoop}" HADOOP_CONF_DIR="${HADOOP_CONF_DIR:-/opt/hadoop/etc/hadoop}"
LOG=/nexo/evidence/hadoop/flume.log
exec > >(tee "$LOG") 2>&1
run() { echo; echo "\$ $*"; "$@"; }
echo "# Flume NexoUrbano — $(date -u +%FT%TZ)"

rm -rf /tmp/flume && mkdir -p /tmp/flume && : > /tmp/flume/app_live.log
hdfs dfs -rm -r -f -skipTrash /nexo/bronze/logs >/dev/null 2>&1 || true
hdfs dfs -mkdir -p /nexo/bronze/logs

echo "\$ flume-ng agent -n nexo -f /nexo/04-hadoop/flume/nexo-agent.conf (en segundo plano)"
flume-ng agent -n nexo -c "$FLUME_HOME/conf" -f /nexo/04-hadoop/flume/nexo-agent.conf \
  --classpath "$(hadoop classpath)" -Dflume.root.logger=INFO,console > /tmp/flume/agent.log 2>&1 &
AGENT=$!
sleep 20

echo; echo "# Simulando 200 eventos en /tmp/flume/app_live.log (≈ 20 por segundo)"
EVENTOS=(ride_start ride_start ride_start ride_end ride_end ride_end payment_fail)
for i in $(seq 1 200); do
  ev=${EVENTOS[$((RANDOM % ${#EVENTOS[@]}))]}
  printf '{"ts": "%s", "event": "%s", "vehicle_id": "V%04d", "rider_id": "R%04d", "battery_pct": %d.%d}\n' \
    "$(date -u +%FT%T+00:00)" "$ev" $((RANDOM % 80)) $((RANDOM % 120)) $((10 + RANDOM % 90)) $((RANDOM % 10)) >> /tmp/flume/app_live.log
  sleep 0.05
done
echo "líneas escritas: $(wc -l < /tmp/flume/app_live.log)"

echo "# Esperando el roll de archivos del sink HDFS (rollInterval=10 s)..."
sleep 30
kill $AGENT 2>/dev/null; wait $AGENT 2>/dev/null

echo; echo "# Log del agente (extracto)"
grep -E "Creating hdfs|Renaming|Closing|Exception|ERROR" /tmp/flume/agent.log | awk "NR <= 20"

run hdfs dfs -ls -R /nexo/bronze/logs
echo; echo "# Líneas que llegaron a HDFS (deben ser 200):"
hdfs dfs -cat '/nexo/bronze/logs/*/*.jsonl' | wc -l
echo; echo "# Eventos por tipo en HDFS:"
hdfs dfs -cat '/nexo/bronze/logs/*/*.jsonl' | grep -o '"event": "[a-z_]*"' | sort | uniq -c
