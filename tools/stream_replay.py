"""Reproduce data/app.log como stream de archivos JSON (fuente de M9, opción B del enunciado).

Suelta un archivo cada --intervalo segundos en data/stream_in/ con --por-archivo eventos.
Los eventos están separados 3 s en tiempo de evento, así que 10 eventos por archivo = 30 s de
tiempo de evento por cada 2 s reales: las ventanas de 2 min se ven avanzar en la consola.

Inyecta dos eventos tardíos a propósito (para documentar el watermark de 1 min):
  - TARDE-ACEPTADO:  payment_fail con ts 40 s antes del máximo visto  -> entra (dentro del watermark)
  - TARDE-DESCARTADO: payment_fail con ts 5 min antes del máximo visto -> Spark lo descarta
Ambos usan vehicle_id V9998 / V9999 para encontrarlos en la salida.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def replay(destino: Path, intervalo: float = 2.0, por_archivo: int = 10, limpiar: bool = True, log=print) -> None:
    eventos = [json.loads(l) for l in (REPO / "data" / "app.log").read_text(encoding="utf-8").splitlines() if l.strip()]
    if limpiar and destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True, exist_ok=True)
    max_ts = None
    n_arch = 0
    for i in range(0, len(eventos), por_archivo):
        lote = eventos[i : i + por_archivo]
        lote_max = max(datetime.fromisoformat(e["ts"]) for e in lote)
        max_ts = lote_max if max_ts is None else max(max_ts, lote_max)
        if n_arch == 20:
            tardio = {"ts": (max_ts - timedelta(seconds=40)).isoformat(), "event": "payment_fail",
                      "vehicle_id": "V9998", "rider_id": "R9998", "battery_pct": 50.0}
            lote = lote + [tardio]
            log(f"[replay] TARDE-ACEPTADO inyectado: ts={tardio['ts']} (max visto {max_ts.isoformat()})")
        if n_arch == 30:
            tardio = {"ts": (max_ts - timedelta(minutes=5)).isoformat(), "event": "payment_fail",
                      "vehicle_id": "V9999", "rider_id": "R9999", "battery_pct": 50.0}
            lote = lote + [tardio]
            log(f"[replay] TARDE-DESCARTADO inyectado: ts={tardio['ts']} (max visto {max_ts.isoformat()}, "
                f"watermark ≈ {(max_ts - timedelta(minutes=1)).isoformat()})")
        tmp = destino / f".lote_{n_arch:04d}.tmp"
        tmp.write_text("\n".join(json.dumps(e) for e in lote) + "\n", encoding="utf-8")
        tmp.rename(destino / f"lote_{n_arch:04d}.json")  # rename atómico: Spark nunca lee un archivo a medias
        n_arch += 1
        time.sleep(intervalo)
    log(f"[replay] fin: {n_arch} archivos, {len(eventos)} eventos")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", default=str(REPO / "data" / "stream_in"))
    ap.add_argument("--intervalo", type=float, default=2.0)
    ap.add_argument("--por-archivo", type=int, default=10)
    a = ap.parse_args()
    replay(Path(a.destino), a.intervalo, a.por_archivo, log=lambda m: print(m, flush=True))
