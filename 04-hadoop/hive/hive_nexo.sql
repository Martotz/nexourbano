-- M6 · Hive sobre HDFS: Bronze externa + Silver interna particionada (squad 2002)
--   docker compose exec -T hive bash /nexo/04-hadoop/hive/hive_run.sh
-- Requiere 04-hadoop/hdfs/hdfs_nexo.sh (deja viajes.csv en /nexo/bronze/viajes_full/).

CREATE DATABASE IF NOT EXISTS nexo;
USE nexo;

-- 1) Tabla EXTERNA: Hive solo guarda el esquema; los datos siguen siendo el CSV de HDFS.
DROP TABLE IF EXISTS bronze_viajes;
CREATE EXTERNAL TABLE bronze_viajes (
  ride_id STRING, ts_start STRING, ts_end STRING, duration_s INT,
  rider_id STRING, vehicle_id STRING, station_start STRING, station_end STRING,
  barrio_start STRING, barrio_end STRING, lat_start DOUBLE, lon_start DOUBLE,
  lat_end DOUBLE, lon_end DOUBLE, km DOUBLE, fare_ars DOUBLE, clima_codigo INT
)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:8020/nexo/bronze/viajes_full'
TBLPROPERTIES ('skip.header.line.count'='1');

SELECT COUNT(*) AS filas_bronze FROM bronze_viajes;

-- 2) Tabla INTERNA (managed) particionada por fecha, en Parquet, con las reglas del contrato.
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;
SET hive.exec.max.dynamic.partitions=500;
SET hive.exec.max.dynamic.partitions.pernode=500;

DROP TABLE IF EXISTS silver_viajes;
CREATE TABLE silver_viajes (
  ride_id STRING, ts_start TIMESTAMP, duration_s INT, rider_id STRING, vehicle_id STRING,
  station_start STRING, station_end STRING, barrio_start STRING, barrio_end STRING,
  km DOUBLE, fare_ars DOUBLE, clima_codigo INT
)
PARTITIONED BY (fecha STRING)
STORED AS PARQUET;

INSERT OVERWRITE TABLE silver_viajes PARTITION (fecha)
SELECT ride_id,
       CAST(regexp_replace(substr(ts_start, 1, 19), 'T', ' ') AS TIMESTAMP) AS ts_start,
       duration_s, rider_id, vehicle_id, station_start, station_end, barrio_start, barrio_end,
       km, fare_ars, clima_codigo,
       substr(ts_start, 1, 10) AS fecha
FROM bronze_viajes
WHERE duration_s BETWEEN 30 AND 14400
  AND station_start IS NOT NULL AND station_end IS NOT NULL
  AND fare_ars >= 0;

SELECT COUNT(*) AS filas_silver FROM silver_viajes;
SHOW PARTITIONS silver_viajes;
DESCRIBE FORMATTED silver_viajes;

-- 3a) Estaciones con más destinos distintos (y volumen)
SELECT station_start,
       COUNT(DISTINCT station_end) AS destinos_distintos,
       COUNT(*) AS viajes
FROM silver_viajes
GROUP BY station_start
ORDER BY destinos_distintos DESC, viajes DESC
LIMIT 10;

-- 3b) Viajes de más de 45 minutos
SELECT l.viajes_mas_45_min,
       ROUND(100 * l.viajes_mas_45_min / t.total, 3) AS pct_del_total,
       l.duracion_media_min
FROM (SELECT COUNT(*) AS viajes_mas_45_min, ROUND(AVG(duration_s) / 60, 1) AS duracion_media_min
      FROM silver_viajes WHERE duration_s > 45 * 60) l
CROSS JOIN (SELECT COUNT(*) AS total FROM silver_viajes) t;

SELECT ride_id, ts_start, station_start, station_end, ROUND(duration_s / 60, 1) AS minutos, fare_ars
FROM silver_viajes
WHERE duration_s > 45 * 60
ORDER BY duration_s DESC
LIMIT 10;

-- 3c) Hora × barrio: conteo y duración media
SELECT HOUR(ts_start) AS hora, barrio_start,
       COUNT(*) AS viajes,
       ROUND(AVG(duration_s) / 60, 2) AS duracion_media_min
FROM silver_viajes
GROUP BY HOUR(ts_start), barrio_start
ORDER BY viajes DESC
LIMIT 20;

-- Insumo de M14 P5: facturación de viajes por mes (Hive)
SELECT substr(fecha, 1, 7) AS mes, COUNT(*) AS viajes, ROUND(SUM(fare_ars), 0) AS facturacion_ars
FROM silver_viajes
GROUP BY substr(fecha, 1, 7)
ORDER BY mes;
