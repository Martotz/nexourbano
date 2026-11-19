-- M6 · Externa vs. interna: qué pasa con los datos al hacer DROP
USE nexo;
DROP TABLE IF EXISTS demo_externa;
DROP TABLE IF EXISTS demo_interna;

CREATE EXTERNAL TABLE demo_externa (linea STRING)
STORED AS TEXTFILE
LOCATION 'hdfs://namenode:8020/nexo/bronze/demo_externa';

CREATE TABLE demo_interna STORED AS TEXTFILE AS SELECT linea FROM demo_externa;

SELECT 'externa' AS tabla, COUNT(*) AS filas FROM demo_externa
UNION ALL
SELECT 'interna', COUNT(*) FROM demo_interna;

DESCRIBE FORMATTED demo_externa;
DESCRIBE FORMATTED demo_interna;
