#!/usr/bin/env bash
# M7 · Comando Sqoop equivalente (DOCUMENTADO, no se ejecuta en el sandbox).
# Sqoop está retirado en Apache Attic desde 2021 y su última versión (1.4.7) no tiene build para Hadoop 3.
# El HMV (tabla CRM en HDFS) se cumple con riders_jdbc.py (Spark JDBC). Ver ADR/004-pig-vs-spark.md y el README.
sqoop import \
  --connect jdbc:mysql://mysql:3306/crm \
  --username root --password-file /user/nexo/.mysql.password \
  --table riders \
  --split-by rider_id -m 4 \
  --target-dir /nexo/bronze/riders_sqoop \
  --delete-target-dir \
  --fields-terminated-by ','
