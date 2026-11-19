-- M12 · Cassandra: series temporales de sensores (squad 2002)
-- RF=1 porque el sandbox tiene 1 nodo. En producción: NetworkTopologyStrategy con RF >= 3 por datacenter.
CREATE KEYSPACE IF NOT EXISTS nexo
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE nexo;

-- Modelada POR QUERY: "lecturas de un vehículo, de la más nueva a la más vieja".
--   partition key  = vehicle_id  -> todas las lecturas de un vehículo viven juntas en un nodo
--   clustering key = ts DESC     -> ordenadas en disco por tiempo, la última lectura sale primera
DROP TABLE IF EXISTS lecturas_vehiculo;
CREATE TABLE lecturas_vehiculo (
  vehicle_id  text,
  ts          timestamp,
  lat         double,
  lon         double,
  battery_pct double,
  temp_c      double,
  status      text,
  PRIMARY KEY ((vehicle_id), ts)
) WITH CLUSTERING ORDER BY (ts DESC)
  AND default_time_to_live = 7776000   -- 90 días: la telemetría vieja se va sola (TTL)
  AND compaction = {'class': 'TimeWindowCompactionStrategy', 'compaction_window_unit': 'DAYS', 'compaction_window_size': 1};

