"""M9 · Spark Structured Streaming: alertas operacionales por ventana (squad 2002).

Fuente: directorio data/stream_in/ (opción B), alimentado por tools/stream_replay.py.
  - parseo JSON: ts, vehicle_id, event, battery_pct (+ rider_id)
  - ventana de 2 min con slide de 30 s, watermark de 1 min sobre ts
  - cuenta payment_fail y battery_low por ventana
  - alerta: >= 7 payment_fail en la ventana (posible viaje fantasma / fraude con pasarela)
            >= 8 battery_low en la ventana (flota cayéndose en la zona)
Sinks: consola (modo update, para ver las ventanas cambiar) y lake/gold/gold_alerts
(modo append: cada ventana se escribe una vez, cuando el watermark la cierra).

    python 05-spark/streaming/stream_alertas.py            # lanza también el replay
    python 05-spark/streaming/stream_alertas.py --sin-replay
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from nexo_common import DATA, LAKE, banner, spark_session  # noqa: E402
from stream_replay import replay  # noqa: E402

from pyspark.sql import functions as F  # noqa: E402

# Umbrales = media + 2 desvíos de la línea base de app.log (8 % payment_fail y 10 % battery_low
# sobre ~40 eventos por ventana de 2 min -> esperados ~3.2 y ~4.0 por ventana).
UMBRAL_PAYMENT_FAIL = 7
UMBRAL_BATTERY_LOW = 8


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default=str(DATA / "stream_in"))
    ap.add_argument("--duracion", type=int, default=200, help="segundos que corre el stream")
    ap.add_argument("--sin-replay", action="store_true")
    a = ap.parse_args()

    entrada = Path(a.entrada)
    salida = LAKE / "gold" / "gold_alerts"
    chk = LAKE / "_checkpoints" / "m9"
    for p in (salida, chk):  # corrida reproducible desde cero
        shutil.rmtree(p, ignore_errors=True)
    entrada.mkdir(parents=True, exist_ok=True)
    for f in entrada.glob("*.json"):
        f.unlink()

    spark = spark_session("m9-streaming", shuffle_partitions=4)
    banner("M9 Structured Streaming · ventana 2 min / slide 30 s / watermark 1 min")

    eventos = (
        spark.readStream.schema("ts STRING, event STRING, vehicle_id STRING, rider_id STRING, battery_pct DOUBLE")
        .option("maxFilesPerTrigger", 1)
        .json(str(entrada))
        .withColumn("ts", F.to_timestamp("ts"))
    )

    ventanas = (
        eventos.withWatermark("ts", "1 minute")
        .groupBy(F.window("ts", "2 minutes", "30 seconds").alias("ventana"))
        .agg(
            F.sum((F.col("event") == "payment_fail").cast("int")).alias("payment_fail"),
            F.sum((F.col("event") == "battery_low").cast("int")).alias("battery_low"),
            F.count("*").alias("eventos"),
            F.collect_set(F.when(F.col("event") == "payment_fail", F.col("vehicle_id"))).alias("vehiculos_payment_fail"),
        )
        .select(
            F.col("ventana.start").alias("inicio"),
            F.col("ventana.end").alias("fin"),
            "eventos", "payment_fail", "battery_low", "vehiculos_payment_fail",
            F.concat_ws(
                " + ",
                F.when(F.col("payment_fail") >= UMBRAL_PAYMENT_FAIL, F.lit("FRAUDE?: ráfaga de payment_fail")),
                F.when(F.col("battery_low") >= UMBRAL_BATTERY_LOW, F.lit("FLOTA: batería baja")),
            ).alias("alerta"),
        )
    )

    consola = (
        ventanas.drop("vehiculos_payment_fail").writeStream.outputMode("update").format("console")
        .option("truncate", False).option("numRows", 12)
        .option("checkpointLocation", str(chk / "consola"))
        .trigger(processingTime="2 seconds").queryName("consola").start()
    )
    gold = (
        ventanas.writeStream.outputMode("append").format("parquet")
        .option("path", str(salida)).option("checkpointLocation", str(chk / "gold"))
        .trigger(processingTime="2 seconds").queryName("gold_alerts").start()
    )

    hilo = None
    if not a.sin_replay:
        hilo = threading.Thread(target=replay, args=(entrada,),
                                kwargs={"limpiar": False, "log": lambda m: print(m, flush=True)}, daemon=True)
        hilo.start()

    fin = time.time() + a.duracion
    ultimo = -1
    while time.time() < fin and (hilo is None or hilo.is_alive()):
        time.sleep(5)
        prog = gold.lastProgress
        if prog and prog["batchId"] != ultimo:
            ultimo = prog["batchId"]
            print(f"[progreso] batch={prog['batchId']} filas_in={prog['numInputRows']} "
                  f"watermark={prog.get('eventTime', {}).get('watermark')}", flush=True)

    for q in (consola, gold):
        q.processAllAvailable()
    # recentProgress guarda los últimos 100 micro-batches: se suman todas las filas descartadas
    descartados = sum(o.get("numRowsDroppedByWatermark", 0) for p in gold.recentProgress for o in p.get("stateOperators", []))
    batches_con_descarte = [p["batchId"] for p in gold.recentProgress
                            if any(o.get("numRowsDroppedByWatermark", 0) for o in p.get("stateOperators", []))]
    for q in (consola, gold):
        q.stop()

    banner("Resultado gold_alerts (ventanas cerradas por el watermark)")
    alertas = spark.read.parquet(str(salida)).orderBy("inicio")
    print(f"ventanas escritas: {alertas.count()} · con alerta: {alertas.filter(F.col('alerta') != '').count()}")
    alertas.filter(F.col("alerta") != "").drop("vehiculos_payment_fail").show(30, truncate=False)

    contiene = lambda v: alertas.filter(F.array_contains("vehiculos_payment_fail", v)).count()
    resumen = {
        "filas_descartadas_por_watermark_total": descartados,
        "micro_batches_con_descarte": batches_con_descarte,
        "V9998_tarde_40s_presente_en_ventanas": contiene("V9998"),
        "V9999_tarde_5min_presente_en_ventanas": contiene("V9999"),
    }
    print(json.dumps(resumen, indent=2))
    print("Lectura: V9998 llegó 40 s tarde (dentro del watermark de 1 min) y se contó. V9999 llegó 5 min tarde: "
          "sus ventanas ya estaban cerradas y Spark lo descartó (no aparece en ninguna ventana).")
    spark.stop()


if __name__ == "__main__":
    main()
