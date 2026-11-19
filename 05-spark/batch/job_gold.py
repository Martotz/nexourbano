"""M8 · Spark batch: Bronze -> Silver -> Gold de operaciones (squad 2002).

Entradas
  bronze  data/viajes.csv (1 M filas, seed 2002) o --input (p. ej. hdfs://namenode:8020/nexo/bronze/viajes)
  silver  lake/silver/silver_clima_horario  (M3, Open-Meteo)   -> si falta: clima_codigo del generador
  bronze  lake/bronze/riders_jdbc           (M7, MySQL vía JDBC) -> si falta: data/riders.csv
  bronze  data/ventas.csv                   (revenue de pases/accesorios)

Salidas (Delta si hay jars, si no Parquet) en lake/
  silver/silver_viajes            viajes válidos, particionado por fecha
  silver/silver_viajes_rechazos   filas que violan contratos/bronze_viajes.yaml, con motivo
  gold/gold_ops_diaria            1 fila por día
  gold/gold_top_estaciones        top 10 estaciones origen (total y por día)
  gold/gold_demanda_estacion_hora demanda media por estación × hora del día × clima (para M14 P1)
  05-spark/batch/explain.txt      plan físico anotado
"""

from __future__ import annotations

import argparse
import contextlib
import io
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from nexo_common import DATA, FORMAT, REPO, banner, lake_path, read_table, spark_session, table_exists, write_table  # noqa: E402

from pyspark.sql import Window  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

HERE = Path(__file__).resolve().parent


def leer_viajes(spark, path: str):
    schema = (
        "ride_id STRING, ts_start TIMESTAMP, ts_end TIMESTAMP, duration_s INT, rider_id STRING, vehicle_id STRING, "
        "station_start STRING, station_end STRING, barrio_start STRING, barrio_end STRING, lat_start DOUBLE, "
        "lon_start DOUBLE, lat_end DOUBLE, lon_end DOUBLE, km DOUBLE, fare_ars DOUBLE, clima_codigo INT"
    )
    return spark.read.option("header", True).schema(schema).csv(path)


def calidad(v):
    """Reglas de rechazo de contratos/bronze_viajes.yaml -> columna motivo (null = válido)."""
    motivo = (
        F.when(F.col("ride_id").isNull(), "ride_id nulo")
        .when(F.col("ts_start").isNull() | F.col("ts_end").isNull(), "timestamp nulo")
        .when(F.col("duration_s") < 30, "duration_s < 30")
        .when(F.col("duration_s") > 14400, "duration_s > 4 h")
        .when(F.col("ts_end") < F.col("ts_start"), "ts_end < ts_start")
        .when(F.col("station_start").isNull() | F.col("station_end").isNull(), "estación nula")
        .when(F.col("fare_ars") < 0, "fare_ars < 0")
        .when((F.col("km") == 0) & (F.col("duration_s") > 600), "km = 0 con > 10 min")
    )
    w = Window.partitionBy("ride_id").orderBy("ts_start")
    return (
        v.withColumn("_dup", F.row_number().over(w) > 1)
        .withColumn("motivo", F.when(F.col("_dup"), "ride_id duplicado").otherwise(motivo))
        .drop("_dup")
    )


def clima_horario(spark):
    """Clima a nivel ciudad por hora: promedio de las 3 estaciones consultadas en M3."""
    if table_exists("silver", "silver_clima_horario"):
        c = read_table(spark, "silver", "silver_clima_horario")
        print("clima: silver_clima_horario (Open-Meteo, M3)")
        return c.groupBy("ts_hora").agg(
            F.round(F.avg("temp_c"), 1).alias("temp_c"),
            F.round(F.avg("precip_mm"), 2).alias("precip_mm"),
            F.max("weather_code").alias("weather_code"),
            F.max(F.col("adverso").cast("int")).cast("boolean").alias("clima_adverso"),
        ).withColumn("fuente_clima", F.lit("open-meteo"))
    print("clima: NO hay silver_clima_horario -> se usa clima_codigo del generador (documentado en el README)")
    return None


def riders(spark):
    p = lake_path("bronze", "riders_jdbc")
    if Path(p).exists():
        print("riders: lake/bronze/riders_jdbc (MySQL vía Spark JDBC, M7)")
        return spark.read.parquet(p).select("rider_id", "plan")
    print("riders: data/riders.csv")
    return spark.read.option("header", True).csv(str(DATA / "riders.csv")).select("rider_id", "plan")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(DATA / "viajes.csv"))
    a = ap.parse_args()

    t0 = time.time()
    spark = spark_session("m8-job-gold", shuffle_partitions=16)
    banner(f"M8 job_gold · formato={FORMAT} · input={a.input}")

    # ---------------- Bronze -> Silver
    bronze = leer_viajes(spark, a.input)
    marcado = calidad(bronze).cache()
    total = marcado.count()
    rechazos = marcado.filter(F.col("motivo").isNotNull())
    validos = marcado.filter(F.col("motivo").isNull()).drop("motivo").withColumn("fecha", F.to_date("ts_start"))
    print(f"bronze={total:,}")
    rechazos.groupBy("motivo").count().orderBy(F.desc("count")).show(truncate=False)

    write_table(rechazos, "silver", "silver_viajes_rechazos")
    write_table(validos, "silver", "silver_viajes", partition_by=["fecha"])
    silver = read_table(spark, "silver", "silver_viajes").cache()
    n_silver = silver.count()
    print(f"silver_viajes={n_silver:,} ({100*n_silver/total:.2f} % de bronze)")

    # ---------------- Enriquecimiento: clima + riders (dimensiones chicas -> broadcast)
    clima = clima_horario(spark)
    v = silver.withColumn("ts_hora", F.date_trunc("hour", "ts_start"))
    if clima is not None:
        v = v.join(clima, "ts_hora", "left")
        v = v.withColumn("clima_adverso", F.coalesce("clima_adverso", F.col("clima_codigo") >= 51))
    else:
        v = v.withColumn("clima_adverso", F.col("clima_codigo") >= 51).withColumn("fuente_clima", F.lit("generador"))
    v = v.join(riders(spark), "rider_id", "left")

    # ---------------- Gold: operaciones diarias
    ventas = (
        spark.read.option("header", True).option("inferSchema", True).csv(str(DATA / "ventas.csv"))
        .filter(F.col("ciudad") == "Buenos Aires")
        .groupBy(F.to_date("ts").alias("fecha"))
        .agg(F.sum("monto_ars").alias("revenue_ventas_ars"), F.count("*").alias("ventas"))
    )
    diaria = (
        v.groupBy("fecha")
        .agg(
            F.count("*").alias("viajes"),
            F.round(F.sum("duration_s") / 60, 1).alias("minutos"),
            F.round(F.sum("km"), 1).alias("km"),
            F.round(100 * F.avg(F.col("clima_adverso").cast("int")), 2).alias("pct_clima_adverso"),
            F.round(F.sum("fare_ars"), 2).alias("revenue_viajes_ars"),
            F.countDistinct("rider_id").alias("riders_activos"),
            F.countDistinct("vehicle_id").alias("vehiculos_usados"),
            F.round(100 * F.avg((F.col("plan") == "pro").cast("int")), 2).alias("pct_viajes_plan_pro"),
        )
        .join(ventas, "fecha", "left")
        .fillna({"revenue_ventas_ars": 0, "ventas": 0})
        .withColumn("revenue_total_ars", F.round(F.col("revenue_viajes_ars") + F.col("revenue_ventas_ars"), 2))
        .orderBy("fecha")
    )
    write_table(diaria, "gold", "gold_ops_diaria")
    gold = read_table(spark, "gold", "gold_ops_diaria")
    print(f"gold_ops_diaria: {gold.count()} días")
    gold.orderBy(F.desc("fecha")).show(7, truncate=False)

    # Top 10 estaciones origen: total del período y ranking por día
    por_dia = v.groupBy("fecha", "station_start", "barrio_start").agg(F.count("*").alias("viajes"))
    w = Window.partitionBy("fecha").orderBy(F.desc("viajes"))
    top_dia = por_dia.withColumn("rank", F.row_number().over(w)).filter("rank <= 10").withColumn("periodo", F.lit("dia"))
    top_total = (
        v.groupBy("station_start", "barrio_start").agg(F.count("*").alias("viajes"))
        .orderBy(F.desc("viajes")).limit(10)
        .withColumn("rank", F.row_number().over(Window.orderBy(F.desc("viajes"))))
        .withColumn("fecha", F.lit(None).cast("date")).withColumn("periodo", F.lit("total"))
    )
    top = top_dia.unionByName(top_total)
    write_table(top, "gold", "gold_top_estaciones")
    print("Top 10 estaciones origen (período completo):")
    top_total.select("rank", "station_start", "barrio_start", "viajes").show(truncate=False)

    # Demanda por estación × hora del día × clima (insumo de "dónde reponer si llueve")
    horas = v.groupBy("station_start", "fecha", F.hour("ts_start").alias("hora"), "clima_adverso").agg(F.count("*").alias("viajes"))
    demanda = (
        horas.groupBy("station_start", "hora", "clima_adverso")
        .agg(F.round(F.avg("viajes"), 3).alias("viajes_por_hora"), F.count("*").alias("horas_observadas"))
    )
    estaciones = spark.read.option("header", True).option("inferSchema", True).csv(str(DATA / "estaciones.csv"))
    demanda = demanda.join(F.broadcast(estaciones.select(F.col("station_id").alias("station_start"), "barrio", "capacidad")), "station_start")
    write_table(demanda, "gold", "gold_demanda_estacion_hora")
    print("Demanda media por hora según clima:")
    demanda.groupBy("clima_adverso").agg(F.round(F.avg("viajes_por_hora"), 3).alias("viajes_por_hora")).show()

    # ---------------- explain de 1 query (con lo que reescribió Catalyst)
    # Se libera el cache antes: si no, el plan muestra InMemoryTableScan y oculta la poda de particiones.
    silver.unpersist(blocking=True)
    marcado.unpersist(blocking=True)
    silver_lake = read_table(spark, "silver", "silver_viajes")
    consulta = (
        silver_lake.filter(F.col("fecha") >= "2026-05-01")
        .join(F.broadcast(spark.read.option("header", True).csv(str(DATA / "riders.csv")).select("rider_id", "plan")), "rider_id")
        .groupBy("plan").agg(F.count("*").alias("viajes"), F.sum("fare_ars").alias("revenue"))
    )
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        consulta.explain("formatted")
    plan = buf.getvalue()
    chk = lambda txt: "SÍ" if txt in plan else "NO"
    notas = f"""
==================================================================
NOTAS DEL SQUAD (qué reescribió Catalyst / qué cacheamos)
==================================================================
Query: viajes de mayo 2026 en silver_viajes ⨝ riders, agrupado por plan.
(Verificado automáticamente contra el plan de arriba: SÍ = aparece en el plan.)

1. Partition pruning [{chk("PartitionFilters: [isnotnull(fecha")}]: el filtro fecha >= '2026-05-01' baja al
   FileScan como PartitionFilters; Spark lee solo las carpetas fecha=2026-05-* y no las 92 particiones.
2. Broadcast join [{chk("BroadcastHashJoin")}]: riders tiene 120 filas, así que Catalyst elige BroadcastHashJoin
   y evita el shuffle de los {n_silver:,} viajes de Silver (BroadcastExchange del lado chico).
3. Column pruning [{chk("ReadSchema: struct<rider_id:string,fare_ars:double>")}]: el scan lee solo rider_id y
   fare_ars (más la partición fecha), no las 17 columnas: ver ReadSchema del Scan.
4. Agregación en dos fases [{chk("HashAggregate")}]: HashAggregate parcial antes del Exchange y final después.
5. Cache (decisión nuestra): silver_viajes se cachea con .cache() mientras se calculan gold_ops_diaria,
   gold_top_estaciones y gold_demanda_estacion_hora (3 lecturas). Antes de este explain se hace
   unpersist(): con cache el plan muestra InMemoryTableScan y no se ve la poda de particiones.

Formato del lake: {FORMAT}. Tiempo total del job: {time.time()-t0:.1f} s.
"""
    (HERE / "explain.txt").write_text(plan + notas, encoding="utf-8")
    print(plan + notas)
    consulta.show()
    spark.stop()


if __name__ == "__main__":
    main()
