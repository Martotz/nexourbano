# M3 · Databricks y volcado de Internet

`01_ingesta.py` está en formato *Databricks notebook source*: corre igual en Databricks y en local.

## En Databricks Free Edition
1. *Catalog* → `workspace` → `default` → *Create volume* `nexo` → subir `data/viajes.csv` (o `viajes_muestra.csv`).
2. *Workspace* → *Import* → `03-databricks/01_ingesta.py` (o clonar el repo con *Git folder*).
3. Conectar a *Serverless* y *Run all*. Los widgets de arriba traen ciudad, fechas y la ruta del Volume.
4. Escribe Delta en `workspace.nexo_silver.{silver_clima_horario, silver_social, silver_clima_viajes}`.
5. *File → Export → HTML* (y *IPython Notebook*) → guardar en `03-databricks/` con los outputs visibles.

Bluesky es opcional: necesita `BSKY_HANDLE` y una App Password (Settings → Privacy and security → App passwords).
Mastodon no necesita credenciales.

## Local (contenedor tools)
`.\run.ps1 s1.ingesta` → mismo código, escribe en `lake/silver/` y deja `data/menciones_social.txt` para el WordCount.
