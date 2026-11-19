# M4–M7 · Hadoop (sandbox en Docker)

| Componente | Imagen | Para qué |
|---|---|---|
| HDFS + YARN | `apache/hadoop:3.3.6` (namenode, datanode, resourcemanager, nodemanager) | almacenamiento y MapReduce |
| Edge | `nexo-hadoop-edge` = apache/hadoop:3.3.6 + Pig 0.17.0 + Flume 1.11.0 (`docker/hadoop/Dockerfile`) | cliente `hdfs`, `hadoop jar`, `pig`, `flume-ng` |
| Hive | `apache/hive:4.0.1` (HiveServer2, metastore Derby embebido, warehouse en HDFS) | SQL sobre HDFS |
| HBase | `harisekhon/hbase:2.1` (standalone) | serving de estado de flota |

UIs: HDFS http://localhost:9870 · YARN http://localhost:8088 · HiveServer2 http://localhost:10002 · HBase http://localhost:16010

`.\run.ps1 s2` corre todo en orden. Paso a paso:

| Paso | Script | Log |
|---|---|---|
| M4 bootstrap | `bootstrap.sh` | `evidence/hadoop/bootstrap.log` |
| M5 HDFS | `hdfs/hdfs_nexo.sh` | `evidence/hadoop/hdfs_nexo.log` |
| M5 WordCount | `mapreduce/wordcount.sh` | `evidence/hadoop/wordcount.log`, `mapreduce/output/part-r-00000`, `mapreduce/top20_terminos.tsv` |
| M6 HBase | `hbase/gen_hbase_script.py` + `hbase/hbase_run.sh` | `evidence/hadoop/hbase_nexo.log` |
| M6 Hive | `hive/hive_run.sh` (`hive_nexo.sql`, `hive_drop_demo.sql`) | `evidence/hadoop/hive_nexo.log` |
| M7 Pig | `pig/pig_run.sh` (`clean_viajes.pig`) | `evidence/hadoop/pig.log` |
| M7 Sqoop (plan B) | `sqoop/riders_jdbc.py` (Spark JDBC) | `evidence/hadoop/riders_jdbc.log` |
| M7 Flume | `flume/flume_run.sh` (`nexo-agent.conf`) | `evidence/hadoop/flume.log` |

Quiz de 4 V: `quiz_4v.md` → exportar el ranking a `quiz.csv`. ADR: `ADR/002-hadoop-hoy.md`.
