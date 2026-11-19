# M8–M9 · Spark

| | Comando | Salida |
|---|---|---|
| Batch Gold | `.\run.ps1 s3.gold` → `python 05-spark/batch/job_gold.py` | `lake/silver/silver_viajes` (+ rechazos), `lake/gold/gold_ops_diaria`, `gold_top_estaciones`, `gold_demanda_estacion_hora`, `batch/explain.txt` |
| Streaming | `.\run.ps1 s3.stream` → `python 05-spark/streaming/stream_alertas.py` | consola (ventanas cambiando) + `lake/gold/gold_alerts`; log en `evidence/spark/streaming.log` |

## Streaming: decisiones
- Fuente: opción B (directorio). `tools/stream_replay.py` suelta un archivo cada 2 s con 10 eventos (30 s de tiempo de evento): las ventanas avanzan rápido en la demo.
- Ventana 2 min, slide 30 s, watermark 1 min sobre `ts`. Umbrales de alerta = media + 2 desvíos de la línea base (≥ 7 `payment_fail` o ≥ 8 `battery_low`).
- **Evento tardío:** el replay inyecta `V9998` con 40 s de atraso (se cuenta) y `V9999` con 5 min de atraso. Este último llega cuando el watermark ya cerró sus ventanas y Spark lo descarta: `numRowsDroppedByWatermark = 4` (una fila por cada una de las 4 ventanas superpuestas a las que pertenecía) y no aparece en `gold_alerts`.

## Caso de uso (6 líneas): viaje fantasma
1. Un "viaje fantasma" es un desbloqueo cobrado sin viaje real, o una tarjeta robada probando cobros: deja una ráfaga de `payment_fail`.
2. La línea base es ~3 `payment_fail` cada 2 min en toda la flota; 7 o más en una ventana se aleja más de 2 desvíos.
3. La alerta sale con la lista de vehículos involucrados (`vehiculos_payment_fail`), así ops sabe a qué scooters mirar.
4. Al ser ventanas deslizantes cada 30 s, la ráfaga se detecta a lo sumo 30 s + 1 min (watermark) después de terminar.
5. Ops bloquea temporalmente esos vehículos y el pago queda en revisión antes de que se repita.
6. La misma ventana con ≥ 8 `battery_low` avisa de flota cayéndose: se manda la camioneta de recambio a la zona.
