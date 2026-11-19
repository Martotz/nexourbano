"""M7 · Plan B de Sqoop: MySQL crm.riders -> HDFS /nexo/bronze/riders_sqoop/ con Spark JDBC.

Hace lo mismo que el `sqoop import` de sqoop_import.sh (que se deja documentado):
lee la tabla por JDBC en paralelo (partición por columna) y la escribe en HDFS como texto
delimitado por comas, el formato por defecto de Sqoop. También deja una copia Parquet en
lake/bronze/riders_jdbc para el job Gold (M8).

    python 04-hadoop/sqoop/riders_jdbc.py      # en el contenedor tools
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from nexo_common import banner, lake_path, spark_session  # noqa: E402
from pyspark.sql import functions as F  # noqa: E402

HDFS = os.environ.get("HDFS_URI", "hdfs://namenode:8020")
URL = f"jdbc:mysql://{os.environ.get('MYSQL_HOST', 'localhost')}:3306/crm"

spark = spark_session("m7-riders-jdbc")
spark.sparkContext._jsc.hadoopConfiguration().set("dfs.client.use.datanode.hostname", "true")
banner(f"Spark JDBC {URL} -> {HDFS}/nexo/bronze/riders_sqoop")

riders = (
    spark.read.format("jdbc")
    .option("url", URL)
    .option("driver", "com.mysql.cj.jdbc.Driver")
    .option("user", "root")
    .option("password", os.environ["MYSQL_ROOT_PASSWORD"])
    # equivalente a --split-by + -m 4 de Sqoop: 4 lecturas paralelas por rango del número de rider
    # 'query' no se puede combinar con partitionColumn: se usa una subconsulta en dbtable
    .option("dbtable", "(SELECT r.*, CAST(SUBSTRING(rider_id, 2) AS UNSIGNED) AS rider_num FROM riders r) AS t")
    .option("partitionColumn", "rider_num").option("lowerBound", 0).option("upperBound", 120).option("numPartitions", 4)
    .load()
    .drop("rider_num")
)
print(f"filas leídas de MySQL: {riders.count()} · particiones JDBC: {riders.rdd.getNumPartitions()}")
riders.printSchema()
riders.groupBy("plan").count().orderBy("plan").show()

destino = f"{HDFS}/nexo/bronze/riders_sqoop"
riders.write.mode("overwrite").option("header", False).csv(destino)
riders.write.mode("overwrite").parquet(lake_path("bronze", "riders_jdbc"))

leido = spark.read.csv(destino)
print(f"HDFS {destino}: {leido.count()} filas en {len(leido.inputFiles())} archivos")
for f in leido.inputFiles():
    print("  ", f)
leido.show(5, truncate=False)
spark.stop()
