# Perfilado — ecobici

- Archivo: `trips.csv`
- Filas: **2,247,697**
- Perfilado (UTC): 2026-11-19T17:13:16+00:00
- Clave: `Id_recorrido` — duplicados: **0**
- Fecha: `fecha_origen_recorrido` · Duración: `duracion_recorrido`

## Columnas

| columna | tipo | nulos % | cardinalidad | min | p50 | p95 | max | outliers IQR % |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Id_recorrido | string | 0.0 | 2,039,054 |  |  |  |  |  |
| duracion_recorrido | string | 0.0 | 16,621 | 61 | 961 | 3,339 | 2,317,818 | 5.927 |
| fecha_origen_recorrido | timestamp | 0.0 | 2,029,756 |  |  |  |  |  |
| id_estacion_origen | string | 0.0 | 414 |  |  |  |  |  |
| nombre_estacion_origen | string | 0.0 | 399 |  |  |  |  |  |
| direccion_estacion_origen | string | 0.0 | 414 |  |  |  |  |  |
| long_estacion_origen | double | 0.0 | 399 | -58.527 | -58.429 | -58.369 | -58.356 | 0 |
| lat_estacion_origen | double | 0.0 | 442 | -34.688 | -34.601 | -34.553 | -34.537 | 0.62 |
| fecha_destino_recorrido | timestamp | 0.0 | 2,137,421 |  |  |  |  |  |
| id_estacion_destino | string | 0.0 | 414 |  |  |  |  |  |
| nombre_estacion_destino | string | 0.0 | 401 |  |  |  |  |  |
| direccion_estacion_destino | string | 0.005 | 414 |  |  |  |  |  |
| long_estacion_destino | double | 0.0 | 401 | -58.527 | -58.429 | -58.369 | 0 | 0.005 |
| lat_estacion_destino | double | 0.0 | 442 | -34.688 | -34.601 | -34.553 | 0 | 0.702 |
| id_usuario | string | 0.0 | 225,324 |  |  |  |  |  |
| modelo_bicicleta | string | 0.0 | 2 |  |  |  |  |  |
| género | string | 0.0 | 3 |  |  |  |  |  |

## Drift temporal (por mes)

| mes | filas | duracion_media | duracion_p50 |
|---|---|---|---|
| 2026-01 | 299123 | 1494.8 | 1056.0 |
| 2026-02 | 282602 | 1488.1 | 1058.0 |
| 2026-03 | 317517 | 1356.5 | 970.0 |
| 2026-04 | 263494 | 1357.3 | 952.0 |
| 2026-05 | 233646 | 1271.0 | 908.0 |
| 2026-06 | 194774 | 1262.2 | 876.0 |
| 2026-07 | 185273 | 1365.2 | 944.0 |
| 2026-08 | 203196 | 1343.3 | 938.0 |
| 2026-09 | 268072 | 1267.4 | 911.0 |

## Viajes por hora del día

| hora | viajes |
|---:|---:|
| 0 | 44,662 |
| 1 | 33,508 |
| 2 | 19,584 |
| 3 | 12,562 |
| 4 | 11,248 |
| 5 | 19,626 |
| 6 | 38,566 |
| 7 | 81,152 |
| 8 | 92,816 |
| 9 | 81,524 |
| 10 | 73,618 |
| 11 | 87,774 |
| 12 | 121,237 |
| 13 | 135,733 |
| 14 | 132,242 |
| 15 | 156,200 |
| 16 | 190,085 |
| 17 | 213,568 |
| 18 | 201,530 |
| 19 | 151,737 |
| 20 | 127,628 |
| 21 | 95,894 |
| 22 | 71,164 |
| 23 | 54,039 |
