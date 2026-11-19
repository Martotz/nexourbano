# NexoUrbano 2026 — Squad 2002

Lakehouse operacional de micromovilidad eléctrica en Buenos Aires: Bronze / Silver / Gold sobre Azure Data Lake (y MinIO),
Databricks, Hadoop (HDFS, MapReduce, Hive, HBase, Pig, Flume), Spark batch + streaming, MongoDB, Cassandra y Neo4j,
cerrado con un producto que responde 5 preguntas de negocio.

**Squad:** Gabriel Donoso · Julián Spinedi · Agustín Martínez — semilla `--seed 2002` — 1 000 000 de viajes sintéticos + EcoBici real.

> Enunciado: `TP_NexoUrbano_2026.md` del pack de cátedra (no se incluye: el producto no se entrega mezclado con el pack).

## Levantar todo (< 20 min + descargas)

Requisitos: **Docker Desktop** (WSL 2) y PowerShell. No hace falta Python ni Java en Windows: todo corre en contenedores.

```powershell
.\run.ps1 setup    # crea .env con contraseñas aleatorias, construye imágenes, genera 1 M viajes, levanta la base
.\run.ps1 s1       # M1–M3: EcoBici + perfilado + Open-Meteo/Mastodon + Data Lake
.\run.ps1 s2       # M4–M7: Hadoop
.\run.ps1 s3       # M8–M9: Spark batch + streaming
.\run.ps1 s4       # M10–M14: Mongo, Cassandra, Neo4j, producto
.\run.ps1 help     # lista de pasos sueltos (ej. .\run.ps1 s2.hive)
```

Si PowerShell bloquea el script: `Set-ExecutionPolicy -Scope Process Bypass` en la misma ventana.

| Servicio | URL / puerto | Perfil |
|---|---|---|
| MySQL (CRM) | `localhost:3307` (3307 para no chocar con un MySQL local), base `crm` | base |
| MongoDB | `mongodb://localhost:27017` | base |
| MinIO consola | http://localhost:9001 | base |
| Spark UI (mientras corre un job) | http://localhost:4040 | base (`tools`) |
| HDFS / YARN | http://localhost:9870 · http://localhost:8088 | `hadoop` |
| HiveServer2 / HBase | `localhost:10000` · http://localhost:16010 | `hadoop` |
| Cassandra | `localhost:9042` | `cassandra` |
| Neo4j Browser | http://localhost:7474 | `neo4j` |

**RAM:** `run.ps1 s4` apaga Hadoop antes de levantar Cassandra y Neo4j, así entra en 8 GB asignados a Docker.

**Disco:** las imágenes ocupan ~16 GB. Si C: es chico, mover el disco de Docker (Docker Desktop → Settings → VM resources →
Disk image location) a otra unidad antes de `setup`. En la máquina del squad quedó en `D:\DockerData`.

**Sin escribir en la terminal:** doble clic en `tools\lanzar.cmd` corre los pasos escritos en `tools\paso.txt`
(por ejemplo `s2` o `s2.pig s2.flume`) y graba la consola en `evidence\_consola\`.

## Data Lake

- Azure (cuenta `nexourbano2002`, Chile Central): `abfss://bronze@nexourbano2002.dfs.core.windows.net/viajes/2026/11/19/viajes.csv`
- MinIO (espejo local, mismo layout): `s3a://bronze/viajes/2026/11/19/viajes.csv`
- Listados: `evidence/azure/listado_azure.log`, `evidence/azure/listado_minio.log`

## Estructura

| Carpeta | Módulo | Entrada principal |
|---|---|---|
| `01-discovery/` | M1 | `4V.md`, `arquitectura.md`, `perfilado.py` → `perfilado/`, `acta_squad.md` |
| `02-azure-datalake/` | M2 | `subir_bronze.py`, guía del portal |
| `03-databricks/` | M3 | `01_ingesta.py` (notebook Databricks, corre también local) |
| `04-hadoop/` | M4–M7 | `hdfs/`, `mapreduce/`, `hbase/`, `hive/`, `pig/`, `sqoop/`, `flume/` |
| `05-spark/` | M8–M9 | `batch/job_gold.py` + `explain.txt`, `streaming/stream_alertas.py` |
| `06-mongodb/` | M10–M11 | `crud.js`, `agg_ventas.js` |
| `07-cassandra/` | M12 | `schema.cql`, `load.cql`, `queries.cql` |
| `08-neo4j/` | M13 | `prep_grafo.py`, `grafo.cypher`, `queries.cypher` |
| `09-producto/` | M14 | `decision_ops.py` → `decision_ops.md`, `ventas_agg.json` |
| `contratos/` | — | data contracts Bronze, Silver y Gold |
| `ADR/` | — | 8 decisiones (000–007) |
| `evidence/` | — | logs de cada comando (los escribe `run.ps1`) y capturas |
| `docker/`, `docker-compose.yml`, `run.ps1` | — | infraestructura |
| `tools/` | — | generador, helper común, replay del stream |

`data/viajes.csv` (160 MB) y `lake/` no se versionan: se regeneran con `.\run.ps1 setup` y los jobs.

## Demo (8 min)

Video: **TODO link** — guion:

1. **Problema** (45 s): ops no sabe dónde reponer cuando llueve, qué scooter retirar ni si hay fraude.
2. **Arquitectura y 4 V** (60 s): `01-discovery/arquitectura.md`, una V → un motor.
3. **Ingesta lakehouse** (90 s): listado de `bronze/viajes/yyyy/mm/dd` en Azure + notebook Databricks con clima y Mastodon.
4. **Hadoop** (90 s): `hdfs fsck` (2 bloques), top 20 del WordCount (#cobro), DROP externa vs. interna en Hive.
5. **Spark** (90 s): `explain.txt` (poda de particiones + broadcast) y consola del streaming con el evento tardío descartado.
6. **Polyglot** (90 s): Mongo `$lookup` top 5, Cassandra `PER PARTITION LIMIT 1` + query que falla, Neo4j recomendación.
7. **Decisión** (45 s): `09-producto/decision_ops.md`, las 5 respuestas.

## Recortes de alcance (sección 8)

| Recorte | Autorizado por | Detalle |
|---|---|---|
| Sqoop nativo → Spark JDBC | 8.6 | `04-hadoop/sqoop/`, `ADR/004-pig-vs-spark.md` |
| Kafka | 8.2 (opcional) | `ADR/005-ingesta-streaming.md` |

No se recortó el millón de filas (8.4) ni Azure real (8.5).

## Resultados de la corrida completa (2026-11-19)

| Módulo | Resultado | Evidencia |
|---|---|---|
| M1 | EcoBici 2026: 2 247 697 viajes perfilados; sintético 1 M | `01-discovery/perfilado/` |
| M2 | 167,7 MB en `bronze/viajes/2026/11/19/` (Azure + MinIO) | `evidence/azure/` |
| M3 | Open-Meteo 6 624 horas-estación, Mastodon 506 posts → 3 tablas Silver | `evidence/s1/ingesta_local.log` |
| M5 | `viajes.csv` en 2 bloques (128 MB + 33 MB), HEALTHY; WordCount top 20 | `evidence/hadoop/`, `04-hadoop/mapreduce/top20_terminos.tsv` |
| M6 | HBase 80 vehículos + scan mantenimiento; Hive 1 000 000 → 979 827, 92 particiones; DROP externa conserva el CSV, interna lo borra | `evidence/hadoop/hbase_nexo.log`, `hive_nexo.log` |
| M7 | Pig `(979827, 40890)` = mismo resultado que Spark; JDBC 120 riders → HDFS; Flume 200/200 líneas | `evidence/hadoop/pig.log`, `riders_jdbc.log`, `flume.log` |
| M8 | Delta: 979 818 en Silver, 91 días en Gold, explain con poda de particiones + broadcast (90 s) | `evidence/spark/job_gold.log`, `05-spark/batch/explain.txt` |
| M9 | 77 ventanas, 4 alertas; evento 5 min tarde descartado (`numRowsDroppedByWatermark = 4`) | `evidence/spark/streaming.log` |
| M10–M11 | Índice: 4 000 → 482 docs examinados; pipeline → `ventas_agg.json`; `$geoNear` | `evidence/mongodb/` |
| M12 | 6 000 lecturas; `PER PARTITION LIMIT 1`; 2 queries anti-patrón rechazadas | `evidence/cassandra/cassandra.log` |
| M13 | 154 nodos, 1 047 relaciones; camino R0001→R0055→R0099; recomendaciones; 2 triángulos VIAJO_CON | `evidence/neo4j/neo4j.log` |
| M14 | 5 preguntas respondidas cruzando 6 fuentes | `09-producto/decision_ops.md` |

## Limitaciones conocidas (honestidad de datos)

- El dataset sintético reparte los viajes parejo en las 24 h y no correlaciona con el clima real: en P1 la lluvia no cambia la demanda y el reporte lo dice. EcoBici sí tiene estacionalidad (`01-discovery/perfilado/ecobici.md`).
- Los tickets de `texto_ops.txt` no tienen fecha: P5 compara totales, no meses.
- Con RF=1 en Cassandra, ONE y QUORUM se comportan igual; el ADR 006 explica la diferencia con RF=3.

## Checklist de entrega

Ver [CHECKLIST_ENTREGA.md](CHECKLIST_ENTREGA.md).
