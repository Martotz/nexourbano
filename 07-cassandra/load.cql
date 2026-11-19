-- M12 · Carga de >= 5 000 lecturas desde el CSV del generador (montado en /nexo/data)
USE nexo;
COPY lecturas_vehiculo (vehicle_id, ts, lat, lon, battery_pct, temp_c, status)
  FROM '/nexo/data/lecturas_sensores.csv'
  WITH HEADER = true AND DATETIMEFORMAT = '%Y-%m-%dT%H:%M:%S%z';
SELECT COUNT(*) AS lecturas FROM lecturas_vehiculo;
