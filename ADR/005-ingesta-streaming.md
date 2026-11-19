# ADR 005 — Ingesta de eventos: Flume vs. Structured Streaming vs. Kafka

- Estado: aceptada · Módulo: M7 / M9 · Fecha: 2026-11-19

1. **Flume** (`04-hadoop/flume/`): agente que tailea `app.log` y escribe en HDFS; simple, pero solo mueve datos (no agrega ni valida) y su proyecto está casi sin mantenimiento.
2. **Structured Streaming** (`05-spark/streaming/`): procesa con ventanas, watermark y estado; es donde está la lógica de negocio (alertas).
3. **Kafka**: no procesa, es el *log* durable y re-leíble entre productores y consumidores; desacopla la app del pipeline.
4. Flume no tiene replay: si el sink HDFS cae, se pierde lo que estaba en el canal de memoria. Kafka retiene días.
5. En el TP el stream sale de archivos (opción B de M9) para no sumar Kafka al sandbox (recorte 8.2, opcional).
6. **Greenfield 2026:** app → **Kafka** (o Event Hubs en Azure) → **Structured Streaming** → Delta Gold. Flume no entraría.
7. Flume solo tiene sentido para seguir ingiriendo logs a un HDFS existente sin tocar las aplicaciones.
8. El watermark de 1 min se probó: un evento con 5 min de atraso se descartó y uno con 40 s se contó (`evidence/spark/streaming.log`).
