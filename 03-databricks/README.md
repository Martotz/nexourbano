# M3 · Databricks y volcado de Internet

`01_ingesta.py` está en formato *Databricks notebook source*: corre igual en Databricks y en local.

## Corrida en Databricks Free Edition (2026-11-19)

| Notebook | Resultado |
|---|---|
| `00_generar_datos` | Volume `workspace.default.nexo` con los datos del squad; md5 de `viajes.csv` = `bf3f88bf99d5a11a773fa339f2af30f0`, **idéntico** al local |
| `01_ingesta` | Open-Meteo OK (3 estaciones × 2 208 h) → `workspace.nexo_silver.silver_clima_horario`, `silver_clima_viajes` (Delta). `silver_social` queda vacía: el cómputo serverless de Free Edition no resuelve `mastodon.social` (egress restringido); la ingesta social corre en la versión local del mismo notebook (506 posts, `evidence/s1/ingesta_local.log`) |

Exportar con outputs: en cada notebook, *File → Export → HTML* y guardar en `03-databricks/` (`00_generar_datos.html`, `01_ingesta.html`).

## Pasos para reproducir en Databricks Free Edition
1. *Workspace* → ⋮ → *Import* → `03-databricks/00_generar_datos.py` y `01_ingesta.py`.
2. Correr `00_generar_datos` (*Run all*): crea el Volume y genera los datos con seed 2002 (no hace falta subir el CSV).
3. Correr `01_ingesta` en *Serverless* (*Run all*). Los widgets de arriba traen ciudad, fechas y la ruta del Volume.
4. Escribe Delta en `workspace.nexo_silver.{silver_clima_horario, silver_social, silver_clima_viajes}`.
5. *File → Export → HTML* (y *IPython Notebook*) → guardar en `03-databricks/` con los outputs visibles.

Bluesky es opcional: necesita `BSKY_HANDLE` y una App Password (Settings → Privacy and security → App passwords).
Mastodon no necesita credenciales.

## Local (contenedor tools)
`.\run.ps1 s1.ingesta` → mismo código, escribe en `lake/silver/` y deja `data/menciones_social.txt` para el WordCount.
