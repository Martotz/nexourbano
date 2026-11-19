#!/usr/bin/env bash
# M13 · Carga y queries en el contenedor neo4j.
#   docker compose exec -T neo4j bash /nexo/08-neo4j/neo4j_run.sh
set -uo pipefail
mkdir -p /nexo/evidence/neo4j
LOG=/nexo/evidence/neo4j/neo4j.log
exec > >(tee "$LOG") 2>&1
CS="cypher-shell -u neo4j -p ${NEO4J_PASSWORD:-$(echo "$NEO4J_AUTH" | cut -d/ -f2)} --format plain"
echo "# Neo4j NexoUrbano — $(date -u +%FT%TZ)"
for i in $(seq 1 30); do $CS "RETURN 1" >/dev/null 2>&1 && break; echo "esperando Neo4j ($i)..."; sleep 5; done
$CS "CALL dbms.components() YIELD name, versions RETURN name, versions"
echo; echo "################ grafo.cypher ################"
$CS -f /nexo/08-neo4j/grafo.cypher
echo; echo "################ queries.cypher ################"
# --format verbose muestra cada query y su tabla de resultados
cypher-shell -u neo4j -p "$(echo "$NEO4J_AUTH" | cut -d/ -f2)" --format verbose -f /nexo/08-neo4j/queries.cypher
