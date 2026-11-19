"""M1 · Perfilado de datasets de movilidad con Spark.

Mide por columna: tipo inferido, nulos (%), cardinalidad, min/max/p50 y outliers (IQR).
Mide drift temporal: filas y duración media por mes. Escribe un reporte Markdown y un
JSON por dataset en 01-discovery/perfilado/ (se versionan: "el perfilado se versiona").

    python 01-discovery/perfilado.py --dataset sintetico     # data/viajes.csv (seed 2002)
    python 01-discovery/perfilado.py --dataset ecobici       # data/abierto/<recorridos>.csv
    python 01-discovery/perfilado.py --csv ruta.csv --nombre otro
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from nexo_common import DATA, banner, spark_session  # noqa: E402

from pyspark.sql import functions as F  # noqa: E402
from pyspark.sql import types as T  # noqa: E402

OUT = Path(__file__).resolve().parent / "perfilado"


def ecobici_csv() -> Path:
    manifiesto = DATA / "abierto" / "MANIFIESTO_ecobici.json"
    if manifiesto.exists():
        return DATA / "abierto" / json.loads(manifiesto.read_text(encoding="utf-8"))["archivo"]
    cands = [p for p in (DATA / "abierto").glob("*.csv") if "muestra" not in p.name]
    if not cands:
        raise SystemExit("Falta el dataset abierto: correr 01-discovery/descargar_ecobici.py")
    return max(cands, key=lambda p: p.stat().st_size)


def detectar_columnas(cols: list[str]) -> tuple[str | None, str | None]:
    """Devuelve (columna de fecha de inicio, columna de duración) por nombre."""
    fecha = next((c for c in cols if re.search(r"(ts_start|fecha_origen|started_at|start_?time|fecha)", c, re.I)), None)
    dur = next((c for c in cols if re.search(r"(duration|duracion)", c, re.I)), None)
    return fecha, dur


def numerizar(col: str):
    """Castea a double tolerando separador de miles (EcoBici publica '1,234')."""
    return F.regexp_replace(F.col(f"`{col}`").cast("string"), ",", "").cast("double")


def perfilar(spark, csv_path: Path, nombre: str) -> dict:
    banner(f"Perfilado {nombre}: {csv_path}")
    df = spark.read.option("header", True).option("inferSchema", True).option("mode", "PERMISSIVE").csv(str(csv_path))
    df = df.cache()
    n = df.count()
    print(f"filas={n:,} columnas={len(df.columns)}")

    aggs = []
    for c in df.columns:
        q = f"`{c}`"
        aggs += [
            F.sum(F.when(F.col(q).isNull() | (F.trim(F.col(q).cast("string")) == ""), 1).otherwise(0)).alias(f"{c}__nulos"),
            F.approx_count_distinct(F.col(q)).alias(f"{c}__card"),
        ]
    base = df.agg(*aggs).collect()[0].asDict()

    columnas = []
    for field in df.schema.fields:
        c = field.name
        info = {
            "columna": c,
            "tipo": field.dataType.simpleString(),
            "nulos": int(base[f"{c}__nulos"]),
            "nulos_pct": round(100 * base[f"{c}__nulos"] / n, 3) if n else 0,
            "cardinalidad_aprox": int(base[f"{c}__card"]),
        }
        es_num = isinstance(field.dataType, T.NumericType)
        if not es_num and re.search(r"(duracion|duration|lat|lon|km|fare|monto)", c, re.I):
            es_num = True  # números publicados como texto
        if es_num:
            x = numerizar(c)
            r = df.select(x.alias("x")).agg(
                F.min("x").alias("min"),
                F.max("x").alias("max"),
                F.mean("x").alias("media"),
                F.percentile_approx("x", [0.25, 0.5, 0.75, 0.95], 1000).alias("q"),
            ).collect()[0]
            if r["q"] and r["q"][0] is not None:
                q1, p50, q3, p95 = r["q"]
                iqr = q3 - q1
                lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                outl = df.select(x.alias("x")).filter((F.col("x") < lo) | (F.col("x") > hi)).count()
                info.update(
                    min=r["min"], max=r["max"], media=round(r["media"], 3), p50=p50, p95=p95,
                    outliers_iqr=outl, outliers_pct=round(100 * outl / n, 3), rango_iqr=[round(lo, 3), round(hi, 3)],
                )
        columnas.append(info)

    fecha_col, dur_col = detectar_columnas(df.columns)
    drift = []
    if fecha_col:
        ts = F.to_timestamp(F.col(f"`{fecha_col}`").cast("string"))
        agg = [F.count("*").alias("filas")]
        if dur_col:
            agg += [F.round(F.mean(numerizar(dur_col)), 1).alias("duracion_media"),
                    F.round(F.percentile_approx(numerizar(dur_col), 0.5, 1000), 1).alias("duracion_p50")]
        dm = df.withColumn("mes", F.date_format(ts, "yyyy-MM")).groupBy("mes").agg(*agg).orderBy("mes")
        drift = [r.asDict() for r in dm.collect()]
        horas = df.withColumn("hora", F.hour(ts)).groupBy("hora").count().orderBy("hora").collect()
    else:
        horas = []

    dup = None
    id_col = next((c for c in df.columns if re.search(r"^(ride_id|id_recorrido|ride_id|id)$", c, re.I)), None)
    if id_col:
        dup = n - df.select(f"`{id_col}`").distinct().count()

    reporte = {
        "dataset": nombre,
        "archivo": str(csv_path.name),
        "perfilado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "filas": n,
        "columnas": columnas,
        "columna_fecha": fecha_col,
        "columna_duracion": dur_col,
        "columna_id": id_col,
        "duplicados_id": dup,
        "drift_mensual": drift,
        "viajes_por_hora": [r.asDict() for r in horas],
    }
    df.unpersist()
    return reporte


def a_markdown(r: dict) -> str:
    L = [f"# Perfilado — {r['dataset']}", "",
         f"- Archivo: `{r['archivo']}`", f"- Filas: **{r['filas']:,}**",
         f"- Perfilado (UTC): {r['perfilado_utc']}",
         f"- Clave: `{r['columna_id']}` — duplicados: **{r['duplicados_id']}**",
         f"- Fecha: `{r['columna_fecha']}` · Duración: `{r['columna_duracion']}`", "",
         "## Columnas", "",
         "| columna | tipo | nulos % | cardinalidad | min | p50 | p95 | max | outliers IQR % |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for c in r["columnas"]:
        f = lambda k: "" if c.get(k) is None else (f"{c[k]:,.3f}".rstrip("0").rstrip(".") if isinstance(c[k], float) else f"{c[k]}")
        L.append(f"| {c['columna']} | {c['tipo']} | {c['nulos_pct']} | {c['cardinalidad_aprox']:,} | {f('min')} | {f('p50')} | {f('p95')} | {f('max')} | {f('outliers_pct')} |")
    if r["drift_mensual"]:
        L += ["", "## Drift temporal (por mes)", ""]
        keys = list(r["drift_mensual"][0].keys())
        L += ["| " + " | ".join(keys) + " |", "|" + "---|" * len(keys)]
        L += ["| " + " | ".join(str(d[k]) for k in keys) + " |" for d in r["drift_mensual"]]
    if r["viajes_por_hora"]:
        L += ["", "## Viajes por hora del día", "", "| hora | viajes |", "|---:|---:|"]
        L += [f"| {d['hora']} | {d['count']:,} |" for d in r["viajes_por_hora"]]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["sintetico", "ecobici"])
    ap.add_argument("--csv")
    ap.add_argument("--nombre")
    a = ap.parse_args()
    if a.csv:
        path, nombre = Path(a.csv), a.nombre or Path(a.csv).stem
    elif a.dataset == "ecobici":
        path, nombre = ecobici_csv(), "ecobici"
    else:
        path, nombre = DATA / "viajes.csv", "sintetico_seed2002"

    spark = spark_session(f"perfilado-{nombre}")
    r = perfilar(spark, path, nombre)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{nombre}.json").write_text(json.dumps(r, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    md = a_markdown(r)
    (OUT / f"{nombre}.md").write_text(md, encoding="utf-8")
    print(md)
    spark.stop()


if __name__ == "__main__":
    main()
