# ADR 007 — Un motor, una carga de trabajo (polyglot de NexoUrbano)

- Estado: aceptada · Módulos: M3, M8–M13 · Fecha: 2026-11-19

Regla 6 del enunciado: cada tecnología aparece en el producto con su justificación. Hadoop, HBase, Hive, Pig, Sqoop,
Flume y Cassandra ya tienen la suya (ADR 002–006). Acá van los motores que faltaban.

## MongoDB → catálogo comercial (`productos`, `ventas`)
1. Un producto (pase, recarga, casco, seguro) tiene atributos distintos según la categoría: un esquema fijo obligaría a columnas vacías.
2. Precios y stock por ciudad viven anidados en el mismo documento: "pase con tag lluvia, precio y stock en CABA" es 1 lectura, no 3 joins.
3. El índice compuesto `ciudad + categoria` bajó los documentos examinados de 4 000 a 482 (`evidence/mongodb/crud.log`).
4. El pipeline de agregación (`$match`, `$group`, `$lookup`) da la analítica comercial sin sacar los datos de la base.
5. No se usa para telemetría ni para relaciones: eso es de Cassandra y Neo4j.

## Neo4j → grafo social de riders
1. Las preguntas de crecimiento son de relaciones: amigos en común, camino más corto, "viajan juntos pero no son amigos".
2. En SQL eso son self-joins recursivos que crecen con cada salto; en Cypher es un patrón de 1 línea.
3. El fraude por collusion (3 riders que arrancan juntos en < 2 min) es un triángulo: el grafo lo encuentra directo.
4. 154 nodos y 1 047 relaciones cargados con LOAD CSV, sin plugins (`evidence/neo4j/neo4j.log`).
5. No guarda viajes ni métricas: recibe del lake solo las aristas ya agregadas (`08-neo4j/prep_grafo.py`).

## Spark 4 + Delta Lake → Silver y Gold (batch y streaming)
1. Es el motor de transformación del lakehouse: lee Bronze (CSV), valida, une con clima y riders y escribe Delta.
2. Delta da transacciones ACID, esquema forzado y particionado por fecha sobre archivos baratos.
3. El plan físico muestra poda de particiones y broadcast join (`05-spark/batch/explain.txt`): 1 M de filas en ~90 s en una PC.
4. El mismo motor hace streaming con ventanas y watermark, así batch y tiempo real comparten código y reglas de calidad.
5. Reemplaza a MapReduce y Pig para trabajo nuevo (ADR 002 y 004); Hive queda como SQL sobre el legado en HDFS.

## Databricks → ingesta desde Internet y trabajo colaborativo
1. Notebook compartido por el squad, con los outputs guardados: es la evidencia ejecutable de M3.
2. Unity Catalog + Volumes reemplazan a un HDFS propio para la capa Silver en la nube (`workspace.nexo_silver`).
3. Serverless en Free Edition: costo cero, sin administrar clusters.
4. Límite real encontrado: Free Edition restringe la salida a Internet (Mastodon no responde); la ingesta social corre local y el notebook lo informa sin cortarse.
5. En producción se montaría ADLS (`abfss://`) en vez del Volume, con el mismo código.
