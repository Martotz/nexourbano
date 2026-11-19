-- M12 · Queries (squad 2002). Las que respetan la PK funcionan; la anti-patrón falla a propósito.
USE nexo;
TRACING OFF;

-- 1) Últimas 20 lecturas de un vehículo (una partición, ya ordenada por ts DESC: sin sort)
SELECT vehicle_id, ts, battery_pct, temp_c, status
FROM lecturas_vehiculo
WHERE vehicle_id = 'V0011'
LIMIT 20;

-- 2) Rango horario de un vehículo (partición + rango sobre la clustering key)
SELECT vehicle_id, ts, lat, lon, battery_pct, status
FROM lecturas_vehiculo
WHERE vehicle_id = 'V0011'
  AND ts >= '2026-05-01 06:00:00+0000' AND ts < '2026-05-01 12:00:00+0000';

-- 3) Última lectura de CADA vehículo (insumo de "qué vehículo retirar hoy", M14 P2)
SELECT vehicle_id, ts, battery_pct, temp_c, status
FROM lecturas_vehiculo
PER PARTITION LIMIT 1;

-- 4) ANTI-PATRÓN: filtrar por una columna que no es de la PK.
--    Cassandra lo rechaza: tendría que leer TODAS las particiones de TODOS los nodos.
SELECT vehicle_id, ts, battery_pct
FROM lecturas_vehiculo
WHERE battery_pct < 15;

-- 5) ANTI-PATRÓN: rango de tiempo sin indicar la partición (vehicle_id).
SELECT vehicle_id, ts, battery_pct
FROM lecturas_vehiculo
WHERE ts > '2026-05-01 00:00:00+0000';

-- 6) Consistencia: lo que usaríamos para cada caso (ver ADR/006). Con RF=1 ambas leen 1 réplica.
CONSISTENCY ONE;
SELECT vehicle_id, ts, battery_pct FROM lecturas_vehiculo WHERE vehicle_id = 'V0042' LIMIT 1;
CONSISTENCY QUORUM;
SELECT vehicle_id, ts, battery_pct FROM lecturas_vehiculo WHERE vehicle_id = 'V0042' LIMIT 1;
CONSISTENCY ONE;
