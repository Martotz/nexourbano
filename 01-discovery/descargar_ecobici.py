"""M1 · Descarga del dataset abierto real: recorridos de EcoBici (Buenos Aires Data).

Usa la API CKAN del portal para encontrar el archivo "recorridos realizados" más reciente
(o el año pedido) y lo deja en data/abierto/. El CSV completo no se versiona; se guarda
una muestra de 2 000 filas y un manifiesto con URL y fecha de descarga (para ADR 000).

    python 01-discovery/descargar_ecobici.py            # último año publicado
    python 01-discovery/descargar_ecobici.py --year 2024
    python 01-discovery/descargar_ecobici.py --url https://.../recorridos-realizados-2024.zip
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from nexo_common import DATA  # noqa: E402

CKAN = "https://data.buenosaires.gob.ar/api/3/action/package_show?id=bicicletas-publicas"
OUT = DATA / "abierto"
HEADERS = {"User-Agent": "nexourbano-tp-squad2002/1.0 (uso academico)"}


def elegir_recurso(year: int | None) -> dict:
    r = requests.get(CKAN, headers=HEADERS, timeout=60)
    r.raise_for_status()
    recursos = r.json()["result"]["resources"]
    candidatos = []
    for res in recursos:
        texto = f"{res.get('name', '')} {res.get('url', '')}".lower()
        m = re.search(r"recorridos[^0-9]*(20\d\d)", texto)
        if m and res.get("url"):
            candidatos.append((int(m.group(1)), res))
    if not candidatos:
        raise SystemExit("No encontré recursos 'recorridos' en el portal. Usá --url.")
    print("Recursos 'recorridos' publicados:")
    for y, res in sorted(candidatos, key=lambda t: t[0]):
        print(f"  {y}  {res.get('format', '?'):5}  {res['url']}")
    if year:
        candidatos = [c for c in candidatos if c[0] == year] or sys.exit(f"No hay recorridos {year}")
    return max(candidatos, key=lambda t: t[0])[1]


def descargar(url: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    destino = OUT / url.rstrip("/").split("/")[-1].split("?")[0]
    if destino.exists() and destino.stat().st_size > 0:
        print(f"Ya existe {destino.name} ({destino.stat().st_size/1e6:.1f} MB), no se vuelve a bajar")
        return destino
    print(f"Descargando {url}")
    with requests.get(url, headers=HEADERS, stream=True, timeout=600) as r:
        r.raise_for_status()
        total = 0
        with destino.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                total += len(chunk)
                if total % (50 << 20) < (1 << 20):
                    print(f"  {total/1e6:.0f} MB", flush=True)
    print(f"OK {destino} ({destino.stat().st_size/1e6:.1f} MB)")
    return destino


def extraer_csv(archivo: Path) -> Path:
    if archivo.suffix.lower() != ".zip":
        return archivo
    with zipfile.ZipFile(archivo) as z:
        csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not csvs:
            raise SystemExit(f"{archivo.name} no contiene CSV")
        nombre = max(csvs, key=lambda n: z.getinfo(n).file_size)
        destino = OUT / Path(nombre).name
        if not destino.exists():
            print(f"Extrayendo {nombre}")
            with z.open(nombre) as src, destino.open("wb") as dst:
                while chunk := src.read(1 << 20):
                    dst.write(chunk)
        return destino


def muestra(csv_path: Path, n: int = 2000) -> Path:
    destino = OUT / "ecobici_muestra.csv"
    with csv_path.open("r", encoding="utf-8", errors="replace", newline="") as src, destino.open(
        "w", encoding="utf-8", newline=""
    ) as dst:
        for i, line in enumerate(src):
            if i > n:
                break
            dst.write(line)
    return destino


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int)
    ap.add_argument("--url")
    a = ap.parse_args()

    url = a.url or elegir_recurso(a.year)["url"]
    csv_path = extraer_csv(descargar(url))
    with csv_path.open("r", encoding="utf-8", errors="replace") as f:
        filas = sum(1 for _ in f) - 1
    m = muestra(csv_path)
    manifiesto = {
        "dataset": "EcoBici - recorridos realizados (Buenos Aires Data)",
        "portal": "https://data.buenosaires.gob.ar/dataset/bicicletas-publicas",
        "url": url,
        "archivo": csv_path.name,
        "filas": filas,
        "descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "licencia": "CC BY 2.5 AR (Buenos Aires Data)",
    }
    (OUT / "MANIFIESTO_ecobici.json").write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifiesto, indent=2, ensure_ascii=False))
    print(f"Muestra versionable: {m}")


if __name__ == "__main__":
    main()
