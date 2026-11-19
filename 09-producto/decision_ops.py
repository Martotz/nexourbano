"""M14 · Producto Gold: una historia de decisión para el ops manager (squad 2002).

Cruza 6 motores/fuentes para responder las 5 preguntas de negocio:
  P1 ¿Dónde reponer scooters en las próximas 3 h si llueve?   Spark Gold + Open-Meteo forecast
  P2 ¿Qué vehículo hay que retirar hoy?                        Cassandra (última lectura) + SOH de la flota
  P3 ¿Qué pase venderle a un rider?                            MongoDB (ventas/catálogo) + Neo4j (intereses, amigos)
  P4 ¿Hay collusion / fraude social?                           Neo4j
  P5 ¿Cuánto se facturó vs. tickets de soporte "cobro"?        Spark Gold (+ Hive) + WordCount MapReduce

Si una fuente no responde, se dice qué dato faltó; no se inventa el número.
Salida: consola + 09-producto/decision_ops.md

    python 09-producto/decision_ops.py      # en el contenedor tools, con mongo/cassandra/neo4j arriba
"""

from __future__ import annotations

import csv
import json
import os
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from nexo_common import DATA, REPO, read_table, spark_session, table_exists  # noqa: E402

HERE = Path(__file__).resolve().parent
MD: list[str] = []
ESTACIONES = {r["station_id"]: r for r in csv.DictReader(open(DATA / "estaciones.csv", encoding="utf-8"))}
CENTRO = (-34.6037, -58.3816)


def out(s: str = "") -> None:
    print(s, flush=True)
    MD.append(s)


def tabla(filas: list[dict], cols: list[str] | None = None) -> None:
    if not filas:
        out("_(sin filas)_")
        return
    cols = cols or list(filas[0].keys())
    out("| " + " | ".join(cols) + " |")
    out("|" + "---|" * len(cols))
    for f in filas:
        out("| " + " | ".join(str(f.get(c, "")) for c in cols) + " |")


def seccion(titulo: str):
    def deco(fn):
        def wrap(*a, **k):
            out(f"\n## {titulo}\n")
            try:
                fn(*a, **k)
            except Exception as e:  # una fuente caída no tumba el resto del producto
                out(f"> **Dato faltante:** no se pudo consultar ({type(e).__name__}: {str(e).splitlines()[0][:200]}).")
                traceback.print_exc()
        return wrap
    return deco


# --------------------------------------------------------------------------- P1
@seccion("P1 · ¿Dónde reponer scooters en las próximas 3 h si llueve?  (Spark Gold + Open-Meteo)")
def p1(spark):
    import requests
    from pyspark.sql import functions as F

    ahora = datetime.now(timezone.utc)
    horas = [(ahora + timedelta(hours=h)).hour for h in range(1, 4)]  # Gold está en horas UTC
    pron = None
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=20, params={
            "latitude": CENTRO[0], "longitude": CENTRO[1], "hourly": "precipitation_probability,precipitation,weather_code",
            "forecast_hours": 4, "timezone": "UTC"})
        r.raise_for_status()
        h = r.json()["hourly"]
        pron = [{"hora_utc": t[11:16], "prob_lluvia_%": p, "mm": mm, "wmo": w}
                for t, p, mm, w in zip(h["time"], h["precipitation_probability"], h["precipitation"], h["weather_code"])][1:4]
        out("Pronóstico Open-Meteo (centro de CABA):")
        tabla(pron)
    except Exception as e:
        out(f"> Dato faltante: pronóstico en vivo no disponible ({type(e).__name__}); se responde el escenario 'si llueve'.")
    llueve = bool(pron) and any((p["prob_lluvia_%"] or 0) >= 50 or (p["wmo"] or 0) >= 51 for p in pron)
    out(f"\n¿Se espera lluvia en las próximas 3 h? **{'SÍ' if llueve else 'NO'}**. "
        "Se calcula igual el escenario con lluvia, que es lo que pregunta el board.")

    d = read_table(spark, "gold", "gold_demanda_estacion_hora")
    lluvia = d.filter(F.col("clima_adverso") & F.col("hora").isin(horas))
    seco = d.filter(~F.col("clima_adverso") & F.col("hora").isin(horas))
    ratio = (lluvia.agg(F.avg("viajes_por_hora")).first()[0] or 0) / (seco.agg(F.avg("viajes_por_hora")).first()[0] or 1)
    top = (
        lluvia.groupBy("station_start", "barrio", "capacidad")
        .agg(F.round(F.sum("viajes_por_hora"), 1).alias("viajes_esperados_3h"))
        .withColumn("presion", F.round(F.col("viajes_esperados_3h") / F.col("capacidad"), 2))
        .orderBy(F.desc("presion")).limit(5).collect()
    )
    out(f"\nHoras UTC evaluadas: {horas}. Top 5 estaciones por presión = viajes esperados en 3 h con lluvia / capacidad:")
    tabla([r.asDict() for r in top])
    out(f"\n**Decisión:** reponer primero en {', '.join(f'{r.station_start} ({r.barrio})' for r in top[:3])}. "
        f"Con lluvia la demanda histórica es {ratio:.2f}× la de tiempo seco en esas horas"
        + (" (≈ 1: los datos sintéticos no traen efecto lluvia, así que la priorización sale de demanda base vs. capacidad; "
           "con datos reales de EcoBici este cociente es el que mueve la decisión)." if abs(ratio - 1) < 0.05 else "."))


# --------------------------------------------------------------------------- P2
@seccion("P2 · ¿Qué vehículo hay que retirar hoy?  (Cassandra + SOH de la flota)")
def p2():
    from cassandra.cluster import Cluster

    soh = {r["vehicle_id"]: r for r in csv.DictReader(open(DATA / "vehiculos.csv", encoding="utf-8"))}
    cl = Cluster([os.environ.get("CASSANDRA_HOST", "localhost")], port=int(os.environ.get("CASSANDRA_PORT", 9042)))
    s = cl.connect("nexo")
    filas = s.execute("SELECT vehicle_id, ts, battery_pct, temp_c, status FROM lecturas_vehiculo PER PARTITION LIMIT 1")
    candidatos = []
    for f in filas:
        v = soh.get(f.vehicle_id, {})
        soh_v = float(v.get("soh_bateria", 100))
        motivos = []
        if soh_v < 70:
            motivos.append(f"SOH {soh_v}% < 70%")
        if f.battery_pct < 15:
            motivos.append(f"batería {f.battery_pct}% < 15%")
        if f.temp_c > 35:
            motivos.append(f"temp {f.temp_c}°C > 35°C")
        if v.get("estado") == "mantenimiento":
            motivos.append("ya marcado en mantenimiento")
        if motivos:
            score = (70 - soh_v if soh_v < 70 else 0) + (15 - f.battery_pct if f.battery_pct < 15 else 0) * 2 + \
                    (f.temp_c - 35 if f.temp_c > 35 else 0) + (5 if v.get("estado") == "mantenimiento" else 0)
            candidatos.append({"vehicle_id": f.vehicle_id, "modelo": v.get("modelo"), "ultima_lectura": f.ts.isoformat(timespec="minutes"),
                               "soh_%": soh_v, "bateria_%": f.battery_pct, "temp_c": f.temp_c, "motivos": "; ".join(motivos),
                               "prioridad": round(score, 1)})
    cl.shutdown()
    candidatos.sort(key=lambda x: -x["prioridad"])
    out(f"Última lectura de {len(soh)} vehículos (PER PARTITION LIMIT 1). Reglas: SOH < 70 %, batería < 15 %, temp > 35 °C, "
        f"o ya en mantenimiento. {len(candidatos)} vehículos cumplen al menos una:")
    tabla(candidatos[:10])
    if candidatos:
        out(f"\n**Decisión:** retirar hoy {', '.join(c['vehicle_id'] for c in candidatos[:3])} (mayor prioridad).")


# --------------------------------------------------------------------------- P3
INTERES_A_TAG = {"clima": "lluvia", "running": "pro", "tecnologia": "pro", "musica": "noche", "gastronomia": "noche",
                 "futbol": "noche", "ciclovia": "urbano", "cafe": "urbano", "fotografia": "urbano", "diseno": "urbano"}


@seccion("P3 · ¿Qué pase venderle a un rider?  (MongoDB + Neo4j)")
def p3():
    from neo4j import GraphDatabase
    from pymongo import MongoClient

    db = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"), serverSelectionTimeoutMS=5000)["nexo"]
    pases = list(db.ventas.aggregate([
        {"$match": {"categoria": "pase", "ciudad": "Buenos Aires"}},
        {"$group": {"_id": "$sku", "ventas": {"$sum": 1}}},
        {"$lookup": {"from": "productos", "localField": "_id", "foreignField": "sku", "as": "p"}},
        {"$unwind": "$p"}, {"$match": {"p.activo": True}},
        {"$project": {"_id": 0, "sku": "$_id", "nombre": "$p.nombre", "tags": "$p.tags",
                      "precio": "$p.precios.Buenos Aires", "ventas": 1}},
        {"$sort": {"ventas": -1}},
    ]))
    compras = {d["_id"]: set(d["skus"]) for d in db.ventas.aggregate([
        {"$group": {"_id": "$rider_id", "skus": {"$addToSet": "$sku"}}}])}
    out(f"Catálogo de pases activos ordenado por ventas (Mongo $lookup): {', '.join(p['sku'] for p in pases)}")

    drv = GraphDatabase.driver(os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
                               auth=("neo4j", os.environ.get("NEO4J_PASSWORD", "")))
    with drv.session() as s:
        riders = s.run("""
            MATCH (r:Rider)-[sd:SALE_DE]->()
            WITH r, sum(sd.viajes) AS viajes ORDER BY viajes DESC LIMIT 5
            OPTIONAL MATCH (r)-[:LE_GUSTA]->(i:Interes)
            OPTIONAL MATCH (r)-[:AMIGO_DE]-(f:Rider)
            RETURN r.rider_id AS rider, r.plan AS plan, viajes, collect(DISTINCT i.nombre) AS intereses,
                   collect(DISTINCT f.rider_id) AS amigos""").data()
    drv.close()

    recs = []
    for r in riders:
        tags = {INTERES_A_TAG.get(i) for i in r["intereses"]} | ({"estudiante"} if r["plan"] == "free" else set())
        ya = compras.get(r["rider"], set())
        amigos_compraron = set().union(*(compras.get(f, set()) for f in r["amigos"])) if r["amigos"] else set()
        def score(p):
            return 3 * len(tags & set(p["tags"])) + 2 * (p["sku"] in amigos_compraron) + p["ventas"] / 100
        opciones = sorted((p for p in pases if p["sku"] not in ya), key=score, reverse=True)
        if opciones:
            p = opciones[0]
            recs.append({"rider": r["rider"], "plan": r["plan"], "viajes": r["viajes"], "intereses": ", ".join(r["intereses"]),
                         "pase_sugerido": f"{p['sku']} {p['nombre']}", "tags_pase": ", ".join(p["tags"]),
                         "precio_ars": p["precio"], "lo_compró_un_amigo": p["sku"] in amigos_compraron})
    out("\nTop 5 riders por viajes (Neo4j SALE_DE) → pase que todavía no compraron con más afinidad "
        "(3 pts por tag que coincide con sus intereses, 2 si lo compró un amigo, + popularidad):")
    tabla(recs)


# --------------------------------------------------------------------------- P4
@seccion("P4 · ¿Hay collusion / fraude social?  (Neo4j)")
def p4():
    from neo4j import GraphDatabase

    drv = GraphDatabase.driver(os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
                               auth=("neo4j", os.environ.get("NEO4J_PASSWORD", "")))
    with drv.session() as s:
        tri = s.run("""
            MATCH (a:Rider)-[x:INICIO_SINCRONIZADO]-(b:Rider)-[y:INICIO_SINCRONIZADO]-(c:Rider)-[z:INICIO_SINCRONIZADO]-(a)
            WHERE a.rider_id < b.rider_id AND b.rider_id < c.rider_id
            RETURN a.rider_id AS a, b.rider_id AS b, c.rider_id AS c, round(x.z + y.z + z.z, 2) AS z_total
            ORDER BY z_total DESC""").data()
        pares = s.run("""
            MATCH (a:Rider)-[s:INICIO_SINCRONIZADO]->(b:Rider)
            RETURN a.rider_id AS rider_a, b.rider_id AS rider_b, s.veces AS co_inicios_2min, s.esperado AS esperado, s.z AS z,
                   EXISTS { (a)-[:AMIGO_DE]-(b) } AS son_amigos
            ORDER BY z DESC LIMIT 5""").data()
        vc = s.run("""
            MATCH (a:Rider)-[x:VIAJO_CON]-(b:Rider)-[y:VIAJO_CON]-(c:Rider)-[z:VIAJO_CON]-(a)
            WHERE a.rider_id < b.rider_id AND b.rider_id < c.rider_id
            RETURN a.rider_id AS a, b.rider_id AS b, c.rider_id AS c, x.veces + y.veces + z.veces AS viajes_compartidos""").data()
    drv.close()
    out(f"Triángulos de 3 riders que arrancan en la misma estación con < 2 min, por encima de lo esperable (z ≥ 2.5 en los 3 pares): **{len(tri)}**")
    tabla(tri)
    out("\nPares con más co-inicios por encima de lo esperado:")
    tabla(pares)
    out(f"\nTriángulos de viajes compartidos declarados (VIAJO_CON): **{len(vc)}**")
    tabla(vc)
    out("\n**Decisión:** "
        + ("auditar los triángulos de arriba." if tri else
           "no hay evidencia de collusion de 3 riders en los inicios de viaje; ")
        + (f"revisar a mano {pares[0]['rider_a']}–{pares[0]['rider_b']} (z = {pares[0]['z']}) y los triángulos VIAJO_CON. " if pares else "")
        + "Con 7 140 pares evaluados, varios z ≥ 2.5 son esperables por azar: es una lista para revisar, no una acusación.")


# --------------------------------------------------------------------------- P5
@seccion("P5 · ¿Cuánto se facturó vs. tickets de soporte \"cobro\"?  (Spark Gold + WordCount MapReduce)")
def p5(spark):
    from pyspark.sql import functions as F

    g = read_table(spark, "gold", "gold_ops_diaria")
    mes = (g.groupBy(F.date_format("fecha", "yyyy-MM").alias("mes"))
           .agg(F.sum("viajes").alias("viajes"), F.round(F.sum("revenue_viajes_ars")).alias("viajes_ars"),
                F.round(F.sum("revenue_ventas_ars")).alias("ventas_ars"), F.round(F.sum("revenue_total_ars")).alias("total_ars"))
           .orderBy("mes").collect())
    total = sum(r.total_ars for r in mes)
    out("Facturación por mes (gold_ops_diaria, Spark). La misma cuenta en Hive está en evidence/hadoop/hive_nexo.log "
        "(difiere en unos pocos viajes porque Hive no aplica la regla km = 0 con > 10 min).")
    tabla([{k: (f"{v:,.0f}" if k.endswith("_ars") else v) for k, v in r.asDict().items()} for r in mes])

    wc = REPO / "04-hadoop" / "mapreduce" / "output" / "part-r-00000"
    if not wc.exists():
        out("\n> **Dato faltante:** no está el output de WordCount (correr S2).")
        return
    conteos = {}
    for linea in wc.read_text(encoding="utf-8").splitlines():
        palabra, _, n = linea.rpartition("\t")
        conteos[palabra] = conteos.get(palabra, 0) + int(n)
    # Solo las 8 etiquetas del sistema de tickets; los hashtags de Mastodon (#buenosaires, ...) no son tickets
    etiquetas = ["#bateria", "#freno", "#app", "#cobro", "#gps", "#candado", "#pago", "#rueda"]
    cobro = conteos.get("#cobro", 0)
    pago = conteos.get("#pago", 0)
    tickets = sum(conteos.get(e, 0) for e in etiquetas)
    out(f"\nWordCount sobre {tickets:,} tickets etiquetados: **#cobro = {cobro:,}** ({100*cobro/tickets:.1f} %), "
        f"#pago = {pago:,} ({100*pago/tickets:.1f} %).")
    out(f"\nRelación: **{cobro / (total / 1e6):.2f} tickets de cobro por cada millón de ARS facturado** "
        f"(ARS {total:,.0f} en el período).")
    out("\n> **Dato faltante:** los tickets de `texto_ops.txt` no tienen fecha, así que no se puede ver si los reclamos "
        "por cobro suben en los meses de más facturación. Para eso, el sistema de tickets debería exportar la fecha.")


def main() -> None:
    out(f"# Decisión operativa NexoUrbano — {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
    out("\nGenerado por `09-producto/decision_ops.py` cruzando Spark (Gold), Cassandra, MongoDB, Neo4j, "
        "MapReduce (WordCount) y Open-Meteo.")
    spark = None
    if table_exists("gold", "gold_ops_diaria"):
        spark = spark_session("m14-decision-ops")
    else:
        out("\n> **Dato faltante:** no hay tablas Gold (correr S3 antes). P1 y P5 quedan sin responder.")
    if spark:
        p1(spark)
    p2()
    p3()
    p4()
    if spark:
        p5(spark)
        spark.stop()
    (HERE / "decision_ops.md").write_text("\n".join(MD) + "\n", encoding="utf-8")
    print(f"\nOK -> {HERE / 'decision_ops.md'}")


if __name__ == "__main__":
    main()
