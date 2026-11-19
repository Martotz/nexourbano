"""M6 · Genera hbase_nexo.txt (script de HBase shell) desde data/vehiculos.csv + data/lecturas_sensores.csv.

Rowkey "<bucket>|<vehicle_id>" con bucket = número del vehículo % 4 (ver ADR/003-hbase-rowkey.md).
    python 04-hadoop/hbase/gen_hbase_script.py
"""
import csv
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BUCKETS = 4


def rowkey(vid: str) -> str:
    return f"{int(vid[1:]) % BUCKETS}|{vid}"


ultimo = {}
with open(REPO / "data" / "lecturas_sensores.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["vehicle_id"] not in ultimo or r["ts"] > ultimo[r["vehicle_id"]]["ts"]:
            ultimo[r["vehicle_id"]] = r

with open(REPO / "data" / "vehiculos.csv", encoding="utf-8") as f:
    vehiculos = list(csv.DictReader(f))

L = [
    "# M6 · HBase NexoUrbano (generado por gen_hbase_script.py, no editar a mano)",
    "# docker compose exec -T hbase hbase shell -n /nexo/04-hadoop/hbase/hbase_nexo.txt",
    "disable 'nexo:vehiculos' rescue nil",
    "drop 'nexo:vehiculos' rescue nil",
    "create_namespace 'nexo' rescue nil",
    "# Pre-split en 4 regiones, una por bucket de la rowkey: la escritura se reparte desde el primer put",
    "create 'nexo:vehiculos', {NAME => 'id', VERSIONS => 1}, {NAME => 'telemetry', VERSIONS => 5}, SPLITS => ['1|', '2|', '3|']",
    "describe 'nexo:vehiculos'",
]
for v in vehiculos:
    k, u = rowkey(v["vehicle_id"]), ultimo.get(v["vehicle_id"])
    gps = f"{float(u['lat']):.6f},{float(u['lon']):.6f}" if u else ""
    L += [
        f"put 'nexo:vehiculos', '{k}', 'id:vehicle_id', '{v['vehicle_id']}'",
        f"put 'nexo:vehiculos', '{k}', 'id:modelo', '{v['modelo']}'",
        f"put 'nexo:vehiculos', '{k}', 'telemetry:soh_bateria', '{v['soh_bateria']}'",
        f"put 'nexo:vehiculos', '{k}', 'telemetry:ultimo_gps', '{gps}'",
        f"put 'nexo:vehiculos', '{k}', 'telemetry:estado', '{v['estado']}'",
    ]
ejemplo = vehiculos[11]["vehicle_id"]
L += [
    "count 'nexo:vehiculos'",
    f"# get de un vehículo: la rowkey se calcula igual que al escribir ({ejemplo} -> {rowkey(ejemplo)})",
    f"get 'nexo:vehiculos', '{rowkey(ejemplo)}'",
    "# scan con filtro de estado = mantenimiento",
    "scan 'nexo:vehiculos', {COLUMNS => ['id:vehicle_id', 'id:modelo', 'telemetry:estado', 'telemetry:soh_bateria'], "
    "FILTER => \"SingleColumnValueFilter('telemetry', 'estado', =, 'binary:mantenimiento', true, true)\"}",
    "# scan de un solo bucket (rango de rowkeys): lo que lee una sola región",
    "scan 'nexo:vehiculos', {STARTROW => '2|', STOPROW => '3|', COLUMNS => ['id:vehicle_id'], LIMIT => 5}",
    "exit",
]
out = REPO / "04-hadoop" / "hbase" / "hbase_nexo.txt"
out.write_text("\n".join(L) + "\n", encoding="utf-8")
print(f"OK {out} · {len(vehiculos)} vehículos · {sum(v['estado']=='mantenimiento' for v in vehiculos)} en mantenimiento")
