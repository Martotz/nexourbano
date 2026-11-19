# NexoUrbano 2026 — Squad 2002

Lakehouse operacional de micromovilidad eléctrica (Buenos Aires): Bronze / Silver / Gold sobre Azure Data Lake (o MinIO), Databricks, Hadoop, Spark, MongoDB, Cassandra y Neo4j.

> Enunciado: `TP_NexoUrbano_2026.md` del pack de cátedra (no incluido acá a propósito: el producto no se entrega mezclado con el pack).

## Levantar el entorno (< 20 min)

Requisitos: Docker Desktop, Python 3.10+, Git.

```bash
# 1. Secretos
cp .env.example .env          # Windows PowerShell: Copy-Item .env.example .env
#    editar .env y cambiar las contraseñas

# 2. Datos (data/viajes.csv no se versiona: pesa 40 MB)
python tools/generar_datos.py --seed 2002 --n-viajes 250000 --out data

# 3. Servicios
docker compose up -d mysql mongo minio minio-init
docker compose ps             # mysql y mongo en "healthy"
docker compose up -d neo4j    # cuando lleguemos a S4
docker compose up -d cassandra
```

| Servicio | URL / puerto | Usuario |
|---|---|---|
| MySQL (CRM) | `localhost:3306`, base `crm` | `root` / `MYSQL_ROOT_PASSWORD` |
| MongoDB | `mongodb://localhost:27017` | sin auth (solo local) |
| Cassandra | `localhost:9042` | — |
| Neo4j Browser | http://localhost:7474 | `neo4j` / `NEO4J_PASSWORD` |
| MinIO consola | http://localhost:9001 | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |

Los datos de `data/` se montan en `/import` dentro de mongo, cassandra y neo4j para cargarlos sin copiar archivos a mano.

**RAM:** con 8 GB levantar un NoSQL por vez. Con 16 GB, MySQL + Mongo + Neo4j juntos y Cassandra aparte.

## Data Lake

- URI Bronze: `TODO abfss://bronze@<cuenta>.dfs.core.windows.net/viajes/yyyy/mm/dd/` (o `s3a://bronze/viajes/...` en MinIO)

## Estructura

| Carpeta | Módulo | Sprint |
|---|---|---|
| `01-discovery/` | M1 · 4 V, perfilado, arquitectura | S1 |
| `02-azure-datalake/` | M2 · ADLS Gen2 / MinIO | S1 |
| `03-databricks/` | M3 · ingesta API clima + social | S1 |
| `04-hadoop/` | M4–M7 · HDFS, MapReduce, HBase, Hive, Pig, Sqoop, Flume | S2 |
| `05-spark/` | M8–M9 · batch Gold + Structured Streaming | S3 |
| `06-mongodb/` | M10–M11 · catálogo + agregaciones | S4 |
| `07-cassandra/` | M12 · series temporales | S4 |
| `08-neo4j/` | M13 · grafo social | S4 |
| `09-producto/` | M14 · 5 preguntas de negocio | S4 |
| `contratos/` | data contracts YAML | todos |
| `ADR/` | decisiones de arquitectura | todos |
| `evidence/` | logs y capturas con su comando | todos |

## Demo (8 min)

Link al video: `TODO`

1. Problema de negocio (45 s)
2. Arquitectura y 4 V (60 s)
3. Ingesta lakehouse: Azure + Databricks (90 s)
4. Hadoop como capa batch heredada (90 s)
5. Spark batch + streaming (90 s)
6. Polyglot: Mongo + Cassandra + Neo4j, una query cada uno (90 s)
7. Métricas Gold y la decisión del ops manager (45 s)

## Recortes de alcance

Ninguno por ahora. Si se recorta algo, anotarlo acá con la sección 8 del enunciado que lo autoriza y el ADR correspondiente.

## Checklist de entrega

Ver [CHECKLIST_ENTREGA.md](CHECKLIST_ENTREGA.md).
