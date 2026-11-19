#!/usr/bin/env bash
# M12 · Esquema, carga y queries en el contenedor cassandra.
#   docker compose exec -T cassandra bash /nexo/07-cassandra/cassandra_run.sh
set -uo pipefail
mkdir -p /nexo/evidence/cassandra
LOG=/nexo/evidence/cassandra/cassandra.log
exec > >(tee "$LOG") 2>&1
echo "# Cassandra NexoUrbano — $(date -u +%FT%TZ)"
for i in $(seq 1 40); do cqlsh -e "describe keyspaces" >/dev/null 2>&1 && break; echo "esperando Cassandra ($i)..."; sleep 5; done
cqlsh -e "SELECT release_version FROM system.local"
for f in schema load queries; do
  echo; echo "################ $f.cql ################"
  # cqlsh -f sigue después de un error: así quedan registrados los errores del anti-patrón
  cqlsh -f /nexo/07-cassandra/$f.cql
  if [ "$f" = schema ]; then cqlsh -e "DESCRIBE TABLE nexo.lecturas_vehiculo"; fi
done
echo; echo "# Distribución: en qué token/nodo cae cada partición (vehicle_id) — muestra"
cqlsh -e "SELECT DISTINCT vehicle_id, token(vehicle_id) FROM nexo.lecturas_vehiculo LIMIT 8;"
