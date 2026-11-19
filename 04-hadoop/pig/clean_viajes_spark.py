"""M7 · Las mismas ~10 líneas del script Pig, en Spark (duplicado a propósito, ver ADR/004)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from nexo_common import DATA, spark_session, write_table  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

spark = spark_session("m7-clean-viajes")
v = spark.read.option("header", True).option("inferSchema", True).csv(str(DATA / "viajes.csv"))
rad = lambda c: F.radians(F.col(c))
limpio = (
    v.filter(F.col("duration_s").between(30, 14400))
    .withColumn("km_recta", 2 * 6371 * F.asin(F.sqrt(
        F.sin((rad("lat_end") - rad("lat_start")) / 2) ** 2
        + F.cos(rad("lat_start")) * F.cos(rad("lat_end")) * F.sin((rad("lon_end") - rad("lon_start")) / 2) ** 2)))
    .withColumn("distancia_nula", ((F.col("km") == 0) | (F.col("station_start") == F.col("station_end"))).cast("int"))
    .select("ride_id", "ts_start", "duration_s", "station_start", "station_end", "km", "km_recta", "distancia_nula")
)
write_table(limpio, "silver", "clean_viajes")
limpio.agg(F.count("*").alias("limpios"), F.sum("distancia_nula").alias("con_distancia_nula")).show()
