"""Utilidades compartidas por los scripts del TP NexoUrbano (squad 2002).

- Rutas del repo, de los datos y del lake local (bronze/silver/gold).
- SparkSession con Delta Lake si los jars están disponibles (imagen tools), o Parquet si no.
- Lectura/escritura de tablas del lake con el mismo código en ambos casos.
"""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
LAKE = Path(os.environ.get("NEXO_LAKE", REPO / "lake"))
EVIDENCE = REPO / "evidence"

CIUDAD = os.environ.get("CIUDAD", "Buenos Aires")
SEED = int(os.environ.get("SEED", "2002"))

try:  # .env solo existe en la máquina del squad; dentro de docker ya viene por env_file
    from dotenv import load_dotenv

    load_dotenv(REPO / ".env", override=False)
except ImportError:
    pass

DELTA_JARS = sorted(glob.glob("/opt/jars/delta-*.jar"))
EXTRA_JARS = sorted(glob.glob("/opt/jars/*.jar"))
USE_DELTA = bool(DELTA_JARS) and os.environ.get("NEXO_FORMAT", "delta") == "delta"
FORMAT = "delta" if USE_DELTA else "parquet"


def lake_path(layer: str, table: str) -> str:
    return str(LAKE / layer / table)


def spark_session(app: str, shuffle_partitions: int = 8):
    from pyspark.sql import SparkSession

    b = (
        SparkSession.builder.appName(app)
        .master(os.environ.get("SPARK_MASTER", "local[*]"))
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .config("spark.driver.memory", os.environ.get("SPARK_DRIVER_MEMORY", "2g"))
        .config("spark.ui.showConsoleProgress", "false")
    )
    if EXTRA_JARS:
        b = b.config("spark.jars", ",".join(EXTRA_JARS))
    if USE_DELTA:
        b = b.config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension").config(
            "spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog"
        )
    spark = b.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def write_table(df, layer: str, table: str, mode: str = "overwrite", partition_by: list[str] | None = None) -> str:
    path = lake_path(layer, table)
    w = df.write.format(FORMAT).mode(mode)
    if FORMAT == "delta":
        w = w.option("overwriteSchema", "true")
    if partition_by:
        w = w.partitionBy(*partition_by)
    w.save(path)
    return path


def read_table(spark, layer: str, table: str):
    path = lake_path(layer, table)
    fmt = "delta" if (Path(path) / "_delta_log").exists() else "parquet"
    return spark.read.format(fmt).load(path)


def table_exists(layer: str, table: str) -> bool:
    p = Path(lake_path(layer, table))
    return p.exists() and any(p.iterdir())


def banner(title: str) -> None:
    line = "=" * max(60, len(title) + 8)
    print(f"\n{line}\n=== {title}\n{line}", flush=True)


if __name__ == "__main__":
    print(f"REPO={REPO}\nLAKE={LAKE}\nFORMAT={FORMAT}\nJARS={EXTRA_JARS}", file=sys.stderr)
