# ADR 003 — Rowkey de HBase para `nexo:vehiculos`

- Estado: aceptada · Módulo: M6 · Fecha: 2026-11-19

**Rowkey = `<bucket>|<vehicle_id>`** con `bucket = número del vehículo % 4` (ej. `V0011` → `3|V0011`), tabla pre-partida en 4 regiones (`SPLITS => ['1|','2|','3|']`).

1. Los IDs son secuenciales (V0000, V0001, …): como rowkey directa, las altas nuevas caerían siempre en la última región (hotspot).
2. El prefijo de bucket reparte escrituras y lecturas en 4 regiones desde el primer `put`.
3. El bucket es determinístico: un `get` calcula la rowkey sin buscar (`3|V0011`); no hace falta un índice secundario.
4. No usamos timestamp en la rowkey: la tabla guarda el **estado actual** del vehículo; el historial vive en Cassandra (y en `VERSIONS => 5` de `telemetry`).
5. Costo: un scan "todos los vehículos" toca las 4 regiones; es aceptable porque la consulta típica es por vehículo o por bucket.
