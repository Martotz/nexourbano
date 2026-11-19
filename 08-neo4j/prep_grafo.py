"""M13 · Prepara los CSV que carga grafo.cypher (squad 2002).

Salidas en data/derived/ (Neo4j las lee como file:///derived/...):
  amigos.csv, viajo_con.csv, le_gusta.csv   <- data/grafo.json
  sale_de.csv                               <- top 3 estaciones de origen de cada rider (data/viajes.csv)
  inicio_sincronizado.csv                   <- pares de riders que arrancan viajes en la MISMA estación con
                                               menos de 2 min de diferencia, mucho más seguido de lo esperable
                                               (z de Poisson >= 2.5 contra lo esperado por la actividad de cada uno)

    python 08-neo4j/prep_grafo.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
OUT = DATA / "derived"
VENTANA_S = 120
Z_MIN = 2.5


def co_inicios(v: pd.DataFrame) -> pd.DataFrame:
    """Cuenta, para cada par de riders, cuántas veces arrancaron en la misma estación con < 2 min de diferencia."""
    v = v.sort_values(["station_start", "t"]).reset_index(drop=True)
    st = v["station_start"].to_numpy()
    t = v["t"].to_numpy()
    r = v["rider_id"].to_numpy()
    a_l, b_l = [], []
    k = 1
    while k < 500:  # compara cada viaje con el k-ésimo siguiente mientras alguno siga dentro de la ventana
        ok = (st[k:] == st[:-k]) & ((t[k:] - t[:-k]) < VENTANA_S)
        if not ok.any():
            break
        i = np.nonzero(ok)[0]
        a_l.append(r[i])
        b_l.append(r[i + k])
        k += 1
    a, b = np.concatenate(a_l), np.concatenate(b_l)
    distintos = a != b
    a, b = a[distintos], b[distintos]
    lo, hi = np.minimum(a, b), np.maximum(a, b)
    pares = pd.DataFrame({"a": lo, "b": hi}).value_counts().rename("veces").reset_index()
    # Línea base por par: un rider que viaja mucho coincide más con todos. Esperado(a,b) ∝ viajes_a × viajes_b,
    # escalado para que la suma de esperados sea igual al total observado; z de Poisson = (obs - esp) / sqrt(esp).
    n = v["rider_id"].value_counts()
    ids = np.sort(n.index.to_numpy())
    cnt = n.reindex(ids).to_numpy(dtype=float)
    suma_prod = (cnt.sum() ** 2 - (cnt**2).sum()) / 2  # suma de n_a*n_b sobre todos los pares a<b
    escala = len(a) / suma_prod
    pares["esperado"] = (n.reindex(pares["a"]).to_numpy() * n.reindex(pares["b"]).to_numpy() * escala).round(1)
    pares["z"] = ((pares["veces"] - pares["esperado"]) / np.sqrt(pares["esperado"])).round(2)
    print(f"co-inicios < {VENTANA_S}s: {len(a):,} coincidencias · {len(pares):,} pares con al menos una · "
          f"esperado medio {pares['esperado'].mean():.1f} por par · máximo observado {pares['veces'].max()}")
    return pares


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    g = json.loads((DATA / "grafo.json").read_text(encoding="utf-8"))
    pd.DataFrame(g["amigos"]).to_csv(OUT / "amigos.csv", index=False)
    pd.DataFrame(g["viajo_con"]).to_csv(OUT / "viajo_con.csv", index=False)
    pd.DataFrame(g["le_gusta"]).to_csv(OUT / "le_gusta.csv", index=False)
    print(f"amigos={len(g['amigos'])} viajo_con={len(g['viajo_con'])} le_gusta={len(g['le_gusta'])}")

    v = pd.read_csv(DATA / "viajes.csv", usecols=["ts_start", "rider_id", "station_start", "duration_s"])
    v = v[(v["duration_s"] >= 30) & (v["duration_s"] <= 14400)]
    # segundos desde epoch sin depender de la resolución interna de pandas (ns en 2.x, us en 3.x)
    v["t"] = (pd.to_datetime(v["ts_start"], utc=True) - pd.Timestamp("1970-01-01", tz="UTC")) // pd.Timedelta(seconds=1)

    sale = v.groupby(["rider_id", "station_start"]).size().rename("viajes").reset_index()
    sale = sale.sort_values(["rider_id", "viajes"], ascending=[True, False]).groupby("rider_id").head(3)
    sale.rename(columns={"station_start": "station_id"}).to_csv(OUT / "sale_de.csv", index=False)
    print(f"sale_de (top 3 por rider): {len(sale)} relaciones")

    pares = co_inicios(v)
    sospechosos = pares[pares["z"] >= Z_MIN].sort_values("z", ascending=False)
    sospechosos.to_csv(OUT / "inicio_sincronizado.csv", index=False)
    print(f"inicio_sincronizado (z >= {Z_MIN}): {len(sospechosos)} pares")
    print(sospechosos.head(10).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
