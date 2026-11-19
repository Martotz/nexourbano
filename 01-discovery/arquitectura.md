# Arquitectura medallion — NexoUrbano

```mermaid
flowchart LR
  subgraph Fuentes
    A[Open-Meteo API]
    B[Bluesky / Mastodon]
    C[Dataset abierto EcoBici]
    D[Generador seed 2002]
    E[(MySQL CRM)]
  end
  subgraph Bronze["Bronze · ADLS / MinIO / HDFS"]
    BZ[crudo, particionado yyyy/mm/dd]
  end
  subgraph Silver["Silver · Delta / Hive"]
    SV[validado según contratos/]
  end
  subgraph Gold
    G1[gold_ops_diaria · Spark]
    G2[gold_alerts · Streaming]
  end
  A & B & C --> BZ
  D --> BZ
  E -- Sqoop / JDBC --> BZ
  BZ --> SV --> G1
  D -- stream/*.json --> G2
  SV --> M[(MongoDB catálogo/ventas)]
  SV --> K[(Cassandra lecturas)]
  SV --> N[(Neo4j grafo riders)]
  G1 & G2 & M & K & N --> P[09-producto · 5 preguntas]
```

## Cada V → un motor

| V | Dónde aparece en NexoUrbano | Motor que la resuelve | Por qué |
|---|---|---|---|
| Volumen | | | |
| Variedad | | | |
| Velocidad | | | |
| Veracidad | | | |
