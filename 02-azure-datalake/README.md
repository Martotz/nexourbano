# M2 · Azure Data Lake (ADLS Gen2) — plan B MinIO con el mismo layout

## Azure (cuenta Azure for Students)
1. Portal → *Storage accounts* → *Create*. Suscripción: Azure for Students · Resource group `rg-nexourbano` ·
   nombre `nexourbano2002` (o similar, único global) · región **Brazil South** (o East US, más barata) ·
   *Performance* Standard · *Redundancy* **LRS**.
2. Pestaña *Advanced* → **Enable hierarchical namespace** = ✔ (esto la convierte en ADLS Gen2).
3. Crear contenedores `bronze`, `silver`, `gold` (o dejar que los cree el script).
4. *Security + networking → Access keys* → copiar `key1` a `.env` (`AZURE_STORAGE_ACCOUNT`, `AZURE_STORAGE_KEY`). **Nunca** al repo.
5. `.\run.ps1 s1.lake` sube `viajes_muestra.csv` y `viajes.csv` a `bronze/viajes/yyyy/mm/dd/` y lista los 3 contenedores
   → `evidence/azure/listado_azure.log`. Capturas del portal (suscripción, región, SKU, listado) en `evidence/azure/`.

URI Bronze: `abfss://bronze@<cuenta>.dfs.core.windows.net/viajes/yyyy/mm/dd/viajes.csv` (pegar la real en el README raíz).

## MinIO (plan B, siempre corre)
`minio-init` crea `bronze/silver/gold`; el mismo script sube con el mismo layout → `evidence/azure/listado_minio.log`.
Consola: http://localhost:9001. ADR: `ADR/001-datalake.md`.
