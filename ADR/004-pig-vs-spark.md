# ADR 004 — Limpieza de viajes: Pig vs. Spark (y Sqoop vs. Spark JDBC)

- Estado: aceptada · Módulo: M7 · Fecha: 2026-11-19

## Pig vs. Spark
Las mismas reglas están en `04-hadoop/pig/clean_viajes.pig` y `04-hadoop/pig/clean_viajes_spark.py`: descartar
`duration_s < 30` o `> 4 h`, calcular distancia en línea recta (haversine) y marcar distancia nula
(`km = 0` o misma estación de origen y destino). Spark dio **979 827 viajes limpios y 40 890 con distancia nula**;
la salida de Pig se compara en `evidence/hadoop/pig.log`.

| | Pig | Spark |
|---|---|---|
| Lenguaje | Pig Latin (DSL propio) | Python/SQL, el mismo del resto del lake |
| Motor | Traduce a jobs MapReduce (disco entre etapas) | DAG en memoria, Catalyst optimiza |
| Ecosistema 2026 | Sin releases relevantes; nadie lo contrata | Estándar de facto (Databricks, EMR, Synapse) |
| Tests | Difícil de testear | pytest + DataFrames |

**En producción 2026 queda Spark.** Pig solo se mantiene si hay scripts heredados funcionando y no vale la pena migrarlos.

## Sqoop vs. Spark JDBC (recorte autorizado, sección 8.6)
Sqoop se retiró al Apache Attic en 2021 y la 1.4.7 no corre sobre Hadoop 3. `04-hadoop/sqoop/riders_jdbc.py` hace lo mismo
con `spark.read.jdbc`: 4 lecturas en paralelo por rango (equivalente a `--split-by` + `-m 4`) y escritura en HDFS
`/nexo/bronze/riders_sqoop/` como texto separado por comas (formato por defecto de Sqoop). El comando Sqoop equivalente
queda documentado en `sqoop_import.sh`. Sqoop sigue apareciendo en RFPs viejos porque muchos bancos y telcos tienen
pipelines nocturnos RDBMS → HDFS armados con él hace 10 años.
