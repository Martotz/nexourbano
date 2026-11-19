#!/usr/bin/env bash
# M6 · Ejecuta hbase_nexo.txt en el contenedor hbase y guarda la salida.
#   docker compose exec -T hbase bash /nexo/04-hadoop/hbase/hbase_run.sh
set -uo pipefail
LOG=/nexo/evidence/hadoop/hbase_nexo.log
exec > >(tee "$LOG") 2>&1
echo "# HBase NexoUrbano — $(date -u +%FT%TZ)"
HB=$(command -v hbase || echo /hbase/bin/hbase)
"$HB" version 2>/dev/null | head -1
"$HB" shell -n /nexo/04-hadoop/hbase/hbase_nexo.txt
