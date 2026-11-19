# ADR 002 — Por qué Hadoop sigue en el diseño (y qué no volveríamos a poner en MapReduce)

- Estado: aceptada · Módulo: M4 · Fecha: 2026-11-19

## Contexto
En 2026 el procesamiento nuevo va a Spark/Databricks, pero el board pidió convivir con la capa batch heredada.

## Decisión: Hadoop se queda para
1. **Almacenamiento barato y propio** (HDFS): logs crudos de Flume y Bronze histórico que no conviene pagar en la nube.
2. **Hive legado:** reportes SQL existentes sobre `nexo.silver_viajes`; Spark lee el mismo metastore, sin migración big-bang.
3. **Cumplimiento:** datos de riders (CRM) que por contrato no salen del datacenter propio.

## Qué NO volveríamos a poner en MapReduce en 2026
- Joins y agregaciones de viajes (M8): Spark hace en un job lo que en MR serían varios jobs encadenados escribiendo a disco.
- Cualquier cosa iterativa o en tiempo real: MR solo es batch.
- MapReduce queda solo como ejemplo canónico (WordCount de tickets) y para jobs viejos que ya funcionan.
