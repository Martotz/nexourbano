# Arquitectura medallion — NexoUrbano (squad 2002)

```mermaid
flowchart LR
  subgraph F[Fuentes]
    OM[Open-Meteo API]
    SO[Mastodon / Bluesky]
    EB[EcoBici CABA<br/>dataset abierto]
    GEN[Generador seed 2002<br/>1 M viajes, sensores, ventas]
    MY[(MySQL CRM)]
    LOG[app.log]
  end
  subgraph B[Bronze · crudo]
    ADLS[ADLS Gen2 / MinIO<br/>bronze/viajes/yyyy/mm/dd]
    HDFS[HDFS /nexo/bronze]
  end
  subgraph S[Silver · validado por contrato]
    SV[silver_viajes Delta<br/>partición fecha]
    SC[silver_clima_horario<br/>silver_social]
    HV[Hive silver_viajes<br/>Parquet, partición fecha]
  end
  subgraph G[Gold · decisión]
    GO[gold_ops_diaria<br/>gold_top_estaciones<br/>gold_demanda_estacion_hora]
    GA[gold_alerts streaming]
    WC[wordcount tickets]
  end
  subgraph P[Serving polyglot]
    MO[(MongoDB<br/>catálogo + ventas)]
    CA[(Cassandra<br/>lecturas por vehículo)]
    NE[(Neo4j<br/>grafo de riders)]
    HB[(HBase<br/>estado de flota)]
  end
  OM & SO -->|Databricks / Spark| SC
  EB & GEN --> ADLS
  GEN --> HDFS
  MY -->|Spark JDBC = Sqoop| HDFS
  LOG -->|Flume| HDFS
  ADLS --> SV
  HDFS -->|Hive| HV
  HDFS -->|MapReduce| WC
  SV & SC -->|Spark batch| GO
  LOG -->|Structured Streaming| GA
  GEN --> MO & CA & NE & HB
  GO & GA & WC & MO & CA & NE --> D[09-producto<br/>decision_ops: 5 preguntas]
```

## Cada V → un motor

| V | Dónde aparece en NexoUrbano | Motor | Por qué ese y no otro |
|---|---|---|---|
| **Volumen** | 1 M viajes (160 MB) que crecen todos los días | **Spark** sobre Delta/Parquet particionado por fecha (+ HDFS/ADLS como almacenamiento barato) | Escala horizontal, poda de particiones y broadcast join (ver `05-spark/batch/explain.txt`) |
| **Variedad** | CSV de viajes, JSON anidado de catálogo, texto libre de tickets y redes, grafo social | **MongoDB** (documentos), **MapReduce** (texto), **Neo4j** (relaciones) | Cada forma de dato en el motor que la modela sin forzarla a tablas |
| **Velocidad** | Eventos de app y telemetría que importan en minutos | **Structured Streaming** (ventanas + watermark) y **Cassandra** (escritura y lectura por vehículo en ms) | Alertas en ventana de 2 min; última lectura por partición sin scans |
| **Veracidad** | Viajes absurdos, duplicados, eventos tardíos, bots | **Contrato YAML + Spark** (rechazos con motivo), **watermark**, perfilado versionado | La calidad es código: 2,0 % del Bronze rechazado con motivo en `silver_viajes_rechazos` |

## Capas

| Capa | Dónde | Qué garantiza |
|---|---|---|
| Bronze | ADLS `bronze/` (o MinIO), HDFS `/nexo/bronze` | Dato tal cual llegó, particionado por día de ingesta. Nunca se edita |
| Silver | `lake/silver` (Delta), Hive `nexo.silver_viajes` | Cumple `contratos/*.yaml`: tipos, claves únicas, reglas de rechazo |
| Gold | `lake/gold`, `09-producto/ventas_agg.json`, `04-hadoop/mapreduce/output` | Tablas de decisión con grano de negocio (día, estación × hora, ventana) |
