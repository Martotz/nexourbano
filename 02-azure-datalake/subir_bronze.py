"""M2 · Sube el CSV perfilado a la zona Bronze del Data Lake: Azure ADLS Gen2 o MinIO (plan B).

Layout idéntico en los dos:  bronze/viajes/yyyy/mm/dd/<archivo>   (fecha = día de ingesta, UTC)
Además lista los contenedores bronze/silver/gold y deja el listado en evidence/azure/.

    python 02-azure-datalake/subir_bronze.py --destino azure   # usa AZURE_STORAGE_ACCOUNT / AZURE_STORAGE_KEY de .env
    python 02-azure-datalake/subir_bronze.py --destino minio   # usa MINIO_* de .env
    python 02-azure-datalake/subir_bronze.py --destino ambos
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from nexo_common import DATA, EVIDENCE  # noqa: E402

CONTENEDORES = ["bronze", "silver", "gold"]
ARCHIVOS = [DATA / "viajes_muestra.csv", DATA / "viajes.csv"]


def ruta_bronze(nombre: str) -> str:
    hoy = datetime.now(timezone.utc)
    return f"viajes/{hoy:%Y/%m/%d}/{nombre}"


def azure(log) -> None:
    from azure.storage.filedatalake import DataLakeServiceClient

    cuenta, clave = os.environ["AZURE_STORAGE_ACCOUNT"], os.environ["AZURE_STORAGE_KEY"]
    svc = DataLakeServiceClient(f"https://{cuenta}.dfs.core.windows.net", credential=clave)
    existentes = {fs.name for fs in svc.list_file_systems()}
    for c in CONTENEDORES:
        if c not in existentes:
            svc.create_file_system(c)
            log(f"contenedor creado: {c}")
    fs = svc.get_file_system_client("bronze")
    for f in ARCHIVOS:
        destino = ruta_bronze(f.name)
        with f.open("rb") as data:
            fs.get_file_client(destino).upload_data(data, overwrite=True, max_concurrency=4)
        log(f"subido {f.name} ({f.stat().st_size/1e6:.1f} MB) -> abfss://bronze@{cuenta}.dfs.core.windows.net/{destino}")
    for c in CONTENEDORES:
        log(f"\n$ listado abfss://{c}@{cuenta}.dfs.core.windows.net/")
        for p in svc.get_file_system_client(c).get_paths(recursive=True):
            log(f"  {'DIR ' if p.is_directory else 'FILE'} {p.name}  {p.content_length or ''}  {p.last_modified}")


def minio(log) -> None:
    from minio import Minio

    cli = Minio(os.environ.get("MINIO_ENDPOINT", "localhost:9000").replace("http://", ""),
                access_key=os.environ["MINIO_ROOT_USER"], secret_key=os.environ["MINIO_ROOT_PASSWORD"], secure=False)
    for c in CONTENEDORES:
        if not cli.bucket_exists(c):
            cli.make_bucket(c)
            log(f"bucket creado: {c}")
    for f in ARCHIVOS:
        destino = ruta_bronze(f.name)
        cli.fput_object("bronze", destino, str(f))
        log(f"subido {f.name} ({f.stat().st_size/1e6:.1f} MB) -> s3a://bronze/{destino}")
    for c in CONTENEDORES:
        log(f"\n$ listado s3a://{c}/")
        for o in cli.list_objects(c, recursive=True):
            log(f"  FILE {o.object_name}  {o.size}  {o.last_modified}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--destino", choices=["azure", "minio", "ambos"], default="ambos")
    a = ap.parse_args()
    for nombre, fn in (("azure", azure), ("minio", minio)):
        if a.destino not in (nombre, "ambos"):
            continue
        carpeta = EVIDENCE / "azure"
        carpeta.mkdir(parents=True, exist_ok=True)
        lineas: list[str] = []

        def log(m: str) -> None:
            print(m, flush=True)
            lineas.append(m)

        log(f"# Data Lake {nombre} — {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
        try:
            fn(log)
        except KeyError as e:
            log(f"Falta la variable {e} en .env: se saltea {nombre}.")
        (carpeta / f"listado_{nombre}.log").write_text("\n".join(lineas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
