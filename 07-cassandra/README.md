# M12 · Cassandra: series temporales de sensores

`.\run.ps1 s4.cassandra` → `schema.cql`, `load.cql` (COPY de 6 000 lecturas), `queries.cql`. Log: `evidence/cassandra/cassandra.log`.

- PK `((vehicle_id), ts)` con `CLUSTERING ORDER BY (ts DESC)`: "últimas N lecturas de un vehículo" es leer el principio de una partición.
- `PER PARTITION LIMIT 1` da la última lectura de cada vehículo (insumo de P2 en `09-producto`).
- Queries 4 y 5 fallan **a propósito** (filtro por `battery_pct` y rango de `ts` sin `vehicle_id`): Cassandra pide `ALLOW FILTERING` porque tendría que recorrer todas las particiones.
- TTL de 90 días y TimeWindowCompactionStrategy: la telemetría vieja se va sola y se compacta por día.
- Consistencia ONE vs. QUORUM: `ADR/006-cassandra-consistencia.md`.
