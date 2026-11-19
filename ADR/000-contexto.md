# ADR 000 — Contexto del squad

- Ciudad de operación: **Buenos Aires**
- Dataset abierto de movilidad: **EcoBici — recorridos realizados**, Buenos Aires Data
  (https://data.buenosaires.gob.ar/dataset/bicicletas-publicas). URL exacta del archivo y fecha de descarga:
  `data/abierto/MANIFIESTO_ecobici.json` (lo escribe `01-discovery/descargar_ecobici.py`).
- Semilla `--seed`: **2002** (número de grupo ficticio; **confirmar con la cátedra antes de entregar**)
- Datos: `python tools/generar_datos.py --seed 2002 --n-viajes 1000000` (objetivo de 1 M de filas de M8, sin recorte)
- Integrantes: Gabriel Donoso, Julián Spinedi, Agustín Martínez

Reparto **propuesto** (confirmar en la primera reunión del squad):

| Módulo | Owner | Backup |
|---|---|---|
| Discovery / 4 V | Agustín Martínez | Julián Spinedi |
| Azure Data Lake | Agustín Martínez | Gabriel Donoso |
| Databricks / APIs | Agustín Martínez | Gabriel Donoso |
| Hadoop (HDFS, MR, Hive, HBase, Pig, Sqoop, Flume) | Gabriel Donoso | Agustín Martínez |
| Spark batch + streaming | Gabriel Donoso | Julián Spinedi |
| MongoDB | Julián Spinedi | Agustín Martínez |
| Cassandra | Julián Spinedi | Gabriel Donoso |
| Neo4j | Julián Spinedi | Gabriel Donoso |
| Producto Gold + demo | Agustín Martínez | Los tres |

## Recortes de alcance (sección 8 del enunciado)

| Recorte | Por qué | Documento |
|---|---|---|
| Sqoop nativo → Spark JDBC | Sqoop está retirado (Apache Attic, 2021) y 1.4.7 no tiene build para Hadoop 3 | `04-hadoop/sqoop/`, ADR 004 |
| Kafka (opcional) | No se usa: el stream sale de archivos (opción B de M9) | ADR 005 |
