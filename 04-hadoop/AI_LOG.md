# Bitácora de IA — 04-hadoop (M4–M7)

Herramienta: Claude Opus 5.5 (claude.ai). Bitácora completa del squad: [`/AI_LOG.md`](../AI_LOG.md).

| Fecha | Prompt (resumen) | Qué se aceptó | Qué se corrigió | Qué falló |
|---|---|---|---|---|
| 2026-11-19 | HDFS, WordCount, HBase, Hive, Pig, Sqoop/JDBC, Flume sobre datos NexoUrbano | Scripts de cada subcarpeta y bootstrap.sh | HADOOP_HOME por defecto, awk en vez de head (SIGPIPE), formato de beeline, JDBC con dbtable | Sqoop sin build para Hadoop 3 → plan B Spark JDBC; Pig informa '0 records' (bug de estadísticas, el DUMP da 979 827) |
| | | | _(completar: qué revisó o cambió a mano el owner del módulo)_ | |
