# ADR 001 — Data Lake: on-prem (HDFS/MinIO) vs. cloud (ADLS Gen2)

- Estado: aceptada · Módulo: M2 · Fecha: 2026-11-19

## Contexto
NexoUrbano necesita una zona de landing Bronze/Silver/Gold. Opciones: ADLS Gen2 (Azure for Students) o
almacenamiento propio (HDFS del sandbox / MinIO S3-compatible en Docker).

## Comparación con 4 criterios medibles
Precios de lista de Azure, consultados el 2026-11-19 (confirmar en https://azure.microsoft.com/pricing/calculator/
para la región elegida; las regiones de Sudamérica son más caras que East US).

| Criterio | ADLS Gen2 (Hot, LRS) | On-prem (HDFS / MinIO) |
|---|---|---|
| Costo de 1 TB/mes | ≈ USD 21 (≈ USD 0,0208/GB Hot LRS en East US) + operaciones (cada 10 000 escrituras/lecturas se cobran) | Disco: 1 TB SSD ≈ USD 60 una vez, pero con replicación 3 de HDFS son 3 TB de disco + servidor, energía y operación |
| Egress | Primeros 100 GB/mes gratis; después ≈ USD 0,181/GB saliendo desde Sudamérica (Microsoft Premium Network) | Sin costo por GB; lo limita el enlace propio |
| IAM | Entra ID + RBAC + ACL POSIX por carpeta (`bronze/` solo escritura para ingesta) | HDFS sin Kerberos no tiene autenticación real; MinIO tiene usuarios/políticas S3 pero hay que operarlos |
| Time-to-first-byte | Decenas de ms desde la misma región; peor desde Argentina si la cuenta está en East US | < 1 ms en la red local del sandbox |

## Lo que se creó (2026-11-19)
- Suscripción **Azure for Students**, grupo `rg-nexourbano`, cuenta **`nexourbano2002`**, StorageV2 Standard **LRS**, Hot,
  hierarchical namespace habilitado, región **Chile Central**.
- La suscripción de estudiante tiene la política *Allowed resource deployment regions*: Brazil South y East US fueron
  rechazadas (`RequestDisallowedByAzure`). Chile Central es la región permitida más cercana a Buenos Aires.
- Bronze: `abfss://bronze@nexourbano2002.dfs.core.windows.net/viajes/2026/11/19/viajes.csv` (167,7 MB) — listado en `evidence/azure/listado_azure.log`.

## Decisión
- **Producción:** ADLS Gen2 con hierarchical namespace, contenedores `bronze`, `silver`, `gold` y layout
  `bronze/viajes/yyyy/mm/dd/`. El volumen de NexoUrbano (GB/año) entra holgado y el costo es marginal frente a operar un cluster.
- **Sandbox del TP:** MinIO (imagen `cgr.dev/chainguard/minio`: MinIO retiró las suyas de Docker Hub en 2026) con el mismo layout (lo crea `subir_bronze.py`; imagen `cgr.dev/chainguard/minio` porque MinIO retiró las suyas de Docker Hub en 2026) como plan B y espejo local; HDFS para la parte de Hadoop.

## Qué cambiaría en producción Azure
Autenticación con Managed Identity en vez de account key en `.env`; lifecycle policy que pase Bronze a Cool a los 30 días;
redundancia ZRS; Databricks leyendo `abfss://` con Unity Catalog en vez de montar la cuenta.
