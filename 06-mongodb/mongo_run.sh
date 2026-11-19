#!/usr/bin/env bash
# M10–M11 · Corre crud.js y agg_ventas.js en el contenedor mongo.
#   docker compose exec -T mongo bash /nexo/06-mongodb/mongo_run.sh
set -uo pipefail
mkdir -p /nexo/evidence/mongodb
{ echo "# MongoDB CRUD — $(date -u +%FT%TZ)"; mongosh --quiet --version; mongosh --quiet /nexo/06-mongodb/crud.js; } 2>&1 | tee /nexo/evidence/mongodb/crud.log
{ echo "# MongoDB aggregation — $(date -u +%FT%TZ)"; mongosh --quiet /nexo/06-mongodb/agg_ventas.js; } 2>&1 | tee /nexo/evidence/mongodb/agg_ventas.log
