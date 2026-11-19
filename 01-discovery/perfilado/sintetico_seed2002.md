# Perfilado — sintetico_seed2002

- Archivo: `viajes.csv`
- Filas: **1,000,000**
- Perfilado (UTC): 2026-11-19T17:12:41+00:00
- Clave: `ride_id` — duplicados: **0**
- Fecha: `ts_start` · Duración: `duration_s`

## Columnas

| columna | tipo | nulos % | cardinalidad | min | p50 | p95 | max | outliers IQR % |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| ride_id | string | 0.0 | 987,990 |  |  |  |  |  |
| ts_start | timestamp | 0.0 | 128,766 |  |  |  |  |  |
| ts_end | timestamp | 0.0 | 957,625 |  |  |  |  |  |
| duration_s | int | 0.0 | 2,791 | 8 | 242 | 801 | 20,000 | 5.888 |
| rider_id | string | 0.0 | 110 |  |  |  |  |  |
| vehicle_id | string | 0.0 | 78 |  |  |  |  |  |
| station_start | string | 0.0 | 25 |  |  |  |  |  |
| station_end | string | 0.0 | 25 |  |  |  |  |  |
| barrio_start | string | 0.0 | 12 |  |  |  |  |  |
| barrio_end | string | 0.0 | 12 |  |  |  |  |  |
| lat_start | double | 0.0 | 25 | -34.642 | -34.602 | -34.576 | -34.565 | 0 |
| lon_start | double | 0.0 | 24 | -58.421 | -58.372 | -58.347 | -58.346 | 0 |
| lat_end | double | 0.0 | 25 | -34.642 | -34.602 | -34.576 | -34.565 | 0 |
| lon_end | double | 0.0 | 24 | -58.421 | -58.376 | -58.347 | -58.346 | 0 |
| km | double | 0.0 | 8,667 | 0 | 4.063 | 8.052 | 8.5 | 0 |
| fare_ars | double | 0.0 | 76,011 | 82.8 | 346.9 | 579.66 | 7,419.94 | 1.701 |
| clima_codigo | int | 0.0 | 6 | 0 | 2 | 80 | 80 | 0 |

## Drift temporal (por mes)

| mes | filas | duracion_media | duracion_p50 |
|---|---|---|---|
| 2026-03 | 344500 | 443.9 | 242.0 |
| 2026-04 | 333038 | 443.4 | 243.0 |
| 2026-05 | 322462 | 436.9 | 242.0 |

## Viajes por hora del día

| hora | viajes |
|---:|---:|
| 0 | 41,589 |
| 1 | 41,582 |
| 2 | 41,439 |
| 3 | 41,493 |
| 4 | 41,598 |
| 5 | 41,558 |
| 6 | 41,764 |
| 7 | 42,146 |
| 8 | 41,468 |
| 9 | 41,820 |
| 10 | 41,761 |
| 11 | 41,595 |
| 12 | 41,677 |
| 13 | 41,981 |
| 14 | 41,708 |
| 15 | 42,103 |
| 16 | 41,657 |
| 17 | 41,445 |
| 18 | 41,761 |
| 19 | 42,075 |
| 20 | 41,221 |
| 21 | 41,495 |
| 22 | 41,488 |
| 23 | 41,576 |
