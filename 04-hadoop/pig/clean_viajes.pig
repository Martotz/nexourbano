-- M7 · Pig Latin: limpieza de viajes (squad 2002)
--   pig -x mapreduce -param INPUT=/nexo/bronze/viajes_full -param OUTPUT=/nexo/silver/clean_viajes clean_viajes.pig
-- Mismas reglas que 04-hadoop/pig/clean_viajes_spark.py (ver ADR/004-pig-vs-spark.md).

viajes = LOAD '$INPUT' USING PigStorage(',') AS (
    ride_id:chararray, ts_start:chararray, ts_end:chararray, duration_s:int, rider_id:chararray,
    vehicle_id:chararray, station_start:chararray, station_end:chararray, barrio_start:chararray,
    barrio_end:chararray, lat_start:double, lon_start:double, lat_end:double, lon_end:double,
    km:double, fare_ars:double, clima_codigo:int);

datos   = FILTER viajes BY ride_id != 'ride_id';                       -- fuera el header
validos = FILTER datos BY duration_s >= 30 AND duration_s <= 14400;    -- < 30 s o > 4 h son absurdos
-- distancia en línea recta (haversine, km) y bandera de distancia nula
con_dist = FOREACH validos GENERATE ride_id, ts_start, duration_s, station_start, station_end, km,
    2.0 * 6371.0 * ASIN(SQRT(
        SIN((lat_end - lat_start) * 3.141592653589793 / 360.0) * SIN((lat_end - lat_start) * 3.141592653589793 / 360.0) +
        COS(lat_start * 3.141592653589793 / 180.0) * COS(lat_end * 3.141592653589793 / 180.0) *
        SIN((lon_end - lon_start) * 3.141592653589793 / 360.0) * SIN((lon_end - lon_start) * 3.141592653589793 / 360.0)
    )) AS km_recta:double,
    ((km == 0.0 OR station_start == station_end) ? 1 : 0) AS distancia_nula:int;

STORE con_dist INTO '$OUTPUT' USING PigStorage(',');

todo    = GROUP con_dist ALL;
resumen = FOREACH todo GENERATE COUNT(con_dist) AS limpios, SUM(con_dist.distancia_nula) AS con_distancia_nula;
DUMP resumen;
