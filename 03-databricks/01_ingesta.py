# Databricks notebook source
# MAGIC %md
# MAGIC # NexoUrbano · M3 — Ingesta desde Internet (squad 2002)
# MAGIC
# MAGIC Lee el CSV de viajes (Bronze), consulta **Open-Meteo** (clima horario de las 3 estaciones con más viajes)
# MAGIC y un feed social público (**Mastodon**, y **Bluesky** si hay App Password), y persiste en **Silver**:
# MAGIC
# MAGIC | tabla | grano |
# MAGIC |---|---|
# MAGIC | `silver_clima_horario` | estación × hora |
# MAGIC | `silver_social` | post |
# MAGIC | `silver_clima_viajes` | estación × hora (viajes + clima) |
# MAGIC
# MAGIC El mismo archivo corre en **Databricks** (widgets, Delta en Unity Catalog) y **local** en el contenedor
# MAGIC `tools` (`python 03-databricks/01_ingesta.py`), que escribe en `lake/silver/`.

# COMMAND ----------

import json
import os
import re
import time
from pathlib import Path
from datetime import datetime, timezone

import requests
from pyspark.sql import functions as F
from pyspark.sql import types as T

IS_DBX = "DATABRICKS_RUNTIME_VERSION" in os.environ

# ---- Parámetros (arriba, como pide el enunciado) ----
DEFAULTS = {
    "ciudad": "Buenos Aires",
    "fecha_desde": "2026-03-01",
    "fecha_hasta": "2026-05-31",
    "viajes_path": "/Volumes/workspace/default/nexo/viajes.csv" if IS_DBX else "data/viajes.csv",
    "catalogo": "workspace",
    "schema_silver": "nexo_silver",
    "tags_social": "ecobici,buenosaires,monopatin,scooter,micromovilidad,bicicleta",
}

if IS_DBX:
    for k, v in DEFAULTS.items():
        dbutils.widgets.text(k, v)  # noqa: F821
    P = {k: dbutils.widgets.get(k) for k in DEFAULTS}  # noqa: F821
else:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    from nexo_common import REPO, spark_session, write_table  # noqa: E402

    os.chdir(REPO)
    P = {k: os.environ.get(f"NEXO_{k.upper()}", v) for k, v in DEFAULTS.items()}
    spark = spark_session("m3-ingesta")

print(json.dumps(P, indent=2, ensure_ascii=False))
HTTP = requests.Session()
HTTP.headers["User-Agent"] = "nexourbano-tp-squad2002/1.0 (uso academico)"


def guardar(df, tabla):
    """Silver: Delta en Unity Catalog (Databricks) o Delta/Parquet en lake/silver (local)."""
    if IS_DBX:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {P['catalogo']}.{P['schema_silver']}")
        nombre = f"{P['catalogo']}.{P['schema_silver']}.{tabla}"
        df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(nombre)
    else:
        nombre = write_table(df, "silver", tabla)
    print(f"OK {tabla}: {df.count():,} filas -> {nombre}")


# COMMAND ----------
# MAGIC %md ## 1. Bronze: viajes (CSV)

# COMMAND ----------

viajes = (
    spark.read.option("header", True).option("inferSchema", True).csv(P["viajes_path"])
    .withColumn("ts_start", F.to_timestamp("ts_start"))
    .withColumn("ts_end", F.to_timestamp("ts_end"))
)
n = viajes.count()
print(f"shape = ({n:,}, {len(viajes.columns)})")
nulos = viajes.select([F.sum(F.col(c).isNull().cast("int")).alias(c) for c in viajes.columns])
nulos.show(truncate=False)

# COMMAND ----------
# MAGIC %md ## 2. Cinco métricas de negocio

# COMMAND ----------

validos = viajes.filter((F.col("duration_s") >= 30) & (F.col("duration_s") <= 14400))
print(f"1) viajes válidos: {validos.count():,} de {n:,} ({100*validos.count()/n:.2f} %)")

por_hora = validos.groupBy(F.hour("ts_start").alias("hora")).count()
print(f"2) viajes/hora promedio: {por_hora.agg(F.avg('count')).first()[0] / validos.select(F.to_date('ts_start')).distinct().count():.1f}")

p = validos.agg(F.percentile_approx("duration_s", [0.5, 0.95], 1000).alias("p")).first()["p"]
print(f"3) duración p50 = {p[0]/60:.1f} min · p95 = {p[1]/60:.1f} min")

print("4) top 5 estaciones origen:")
top = validos.groupBy("station_start", "barrio_start").count().orderBy(F.desc("count"))
top.show(5, truncate=False)

print(f"5) facturación total estimada: ARS {validos.agg(F.sum('fare_ars')).first()[0]:,.0f}")

# COMMAND ----------
# MAGIC %md ## 3. Open-Meteo: clima horario de las 3 estaciones con más viajes

# COMMAND ----------

top3 = (
    validos.groupBy("station_start")
    .agg(F.count("*").alias("viajes"), F.first("lat_start").alias("lat"), F.first("lon_start").alias("lon"))
    .orderBy(F.desc("viajes")).limit(3).collect()
)

URL = "https://archive-api.open-meteo.com/v1/archive"
VARS = "temperature_2m,precipitation,rain,weather_code,wind_speed_10m"
filas = []
for est in top3:
    params = {
        "latitude": est["lat"], "longitude": est["lon"],
        "start_date": P["fecha_desde"], "end_date": P["fecha_hasta"],
        "hourly": VARS, "timezone": "UTC",
    }
    r = HTTP.get(URL, params=params, timeout=60)
    r.raise_for_status()
    h = r.json()["hourly"]
    num = lambda v: None if v is None else float(v)  # la API puede mandar 0 (int) o null
    for i, t in enumerate(h["time"]):
        wc = h["weather_code"][i]
        filas.append((est["station_start"], t, num(h["temperature_2m"][i]), num(h["precipitation"][i]),
                      num(h["rain"][i]), None if wc is None else int(wc), num(h["wind_speed_10m"][i])))
    print(f"{est['station_start']} ({est['lat']:.4f},{est['lon']:.4f}): {len(h['time'])} horas")

schema = T.StructType([
    T.StructField("station_id", T.StringType()), T.StructField("hora_txt", T.StringType()),
    T.StructField("temp_c", T.DoubleType()), T.StructField("precip_mm", T.DoubleType()),
    T.StructField("lluvia_mm", T.DoubleType()), T.StructField("weather_code", T.IntegerType()),
    T.StructField("viento_kmh", T.DoubleType()),
])
clima = (
    spark.createDataFrame(filas, schema)
    .withColumn("ts_hora", F.to_timestamp("hora_txt", "yyyy-MM-dd'T'HH:mm")).drop("hora_txt")
    # adverso: llovizna/lluvia/tormenta (WMO >= 51) o más de 0.2 mm en la hora
    .withColumn("adverso", (F.col("weather_code") >= 51) | (F.col("precip_mm") > 0.2))
    .withColumn("fuente", F.lit("open-meteo archive"))
    .withColumn("ingestado_utc", F.current_timestamp())
)
clima.groupBy("station_id").agg(F.count("*").alias("horas"), F.sum(F.col("adverso").cast("int")).alias("horas_adversas"),
                                F.round(F.sum("precip_mm"), 1).alias("mm_total")).show()
guardar(clima, "silver_clima_horario")

# COMMAND ----------
# MAGIC %md ## 4. Feed social público: Mastodon (sin key) + Bluesky (opcional)

# COMMAND ----------

INCIDENTE = re.compile(r"(robo|rob[oa]|choque|accidente|falla|roto|bateri|freno|cobr|estafa|corte|lluvia|tormenta)", re.I)
TAG_HTML = re.compile(r"<[^>]+>")


def mastodon(tag, paginas=4):
    posts, max_id = [], None
    for _ in range(paginas):
        params = {"limit": 40}
        if max_id:
            params["max_id"] = max_id
        r = HTTP.get(f"https://mastodon.social/api/v1/timelines/tag/{tag}", params=params, timeout=30)
        if r.status_code != 200:
            print(f"mastodon #{tag}: HTTP {r.status_code}")
            break
        lote = r.json()
        if not lote:
            break
        for s in lote:
            posts.append(("mastodon", s["id"], s["created_at"], tag, s.get("language"),
                          TAG_HTML.sub(" ", s.get("content") or "").strip(), s.get("url"),
                          s["account"]["acct"]))
        max_id = lote[-1]["id"]
        time.sleep(0.5)
    return posts


def bluesky(q, limit=100):
    h, pw = os.environ.get("BSKY_HANDLE"), os.environ.get("BSKY_APP_PASSWORD")
    if not (h and pw):
        return []
    s = HTTP.post("https://bsky.social/xrpc/com.atproto.server.createSession",
                  json={"identifier": h, "password": pw}, timeout=30)
    s.raise_for_status()
    tok = s.json()["accessJwt"]
    r = HTTP.get("https://bsky.social/xrpc/app.bsky.feed.searchPosts",
                 params={"q": q, "limit": limit}, headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    r.raise_for_status()
    return [("bluesky", p["uri"], p["record"].get("createdAt"), q, (p["record"].get("langs") or [None])[0],
             p["record"].get("text", ""), p["uri"], p["author"]["handle"]) for p in r.json().get("posts", [])]


crudo = []
for tag in P["tags_social"].split(","):
    lote = mastodon(tag.strip())
    print(f"mastodon #{tag}: {len(lote)} posts")
    crudo += lote
for q in ["ecobici", "monopatín eléctrico", "bicisenda Buenos Aires"]:
    lote = bluesky(q)
    if lote:
        print(f"bluesky '{q}': {len(lote)} posts")
    crudo += lote

sch = T.StructType([T.StructField(c, T.StringType()) for c in
                    ["fuente", "post_id", "creado_txt", "consulta", "idioma", "texto", "url", "autor"]])
social = (
    spark.createDataFrame(crudo, sch)
    .dropDuplicates(["fuente", "post_id"])
    .withColumn("creado_utc", F.to_timestamp("creado_txt")).drop("creado_txt")
    .withColumn("texto", F.trim(F.regexp_replace("texto", r"\s+", " ")))
    .filter(F.length("texto") > 0)
    .withColumn("menciona_incidente", F.col("texto").rlike(INCIDENTE.pattern))
    .withColumn("ingestado_utc", F.current_timestamp())
)
social.groupBy("fuente", "consulta").agg(F.count("*").alias("posts"),
                                        F.sum(F.col("menciona_incidente").cast("int")).alias("incidentes")).show(truncate=False)
guardar(social, "silver_social")

if not IS_DBX:  # menciones sociales para el WordCount de M5 (tickets + social)
    textos = [r["texto"] for r in social.select("texto").collect()]
    Path("data/menciones_social.txt").write_text("\n".join(textos) + "\n", encoding="utf-8")
    print(f"data/menciones_social.txt: {len(textos)} líneas")

# COMMAND ----------
# MAGIC %md ## 5. Silver clima × viajes (estación × hora)

# COMMAND ----------

clima_sel = clima.select("station_id", F.col("ts_hora").alias("ts_hora_clima"), "temp_c", "precip_mm",
                         "weather_code", "adverso")
clima_viajes = (
    validos.withColumn("ts_hora", F.date_trunc("hour", "ts_start"))
    .join(F.broadcast(clima_sel),
          (F.col("station_start") == F.col("station_id")) & (F.col("ts_hora") == F.col("ts_hora_clima")), "inner")
    .groupBy("station_id", "ts_hora", "temp_c", "precip_mm", "weather_code", "adverso")
    .agg(F.count("*").alias("viajes"), F.round(F.avg("duration_s") / 60, 2).alias("duracion_media_min"),
         F.round(F.sum("fare_ars"), 2).alias("facturacion_ars"))
)
guardar(clima_viajes, "silver_clima_viajes")

clima_viajes.groupBy("adverso").agg(
    F.count("*").alias("horas"), F.round(F.avg("viajes"), 2).alias("viajes_por_hora"),
    F.round(F.avg("duracion_media_min"), 2).alias("duracion_media_min")).orderBy("adverso").show()
