# Bitácora de IA — NexoUrbano

Squad: 2002
Herramientas usadas (versiones): Claude Opus 5.5 (claude.ai, con ejecución de código)

Regla: una fila por sesión relevante. Mentir acá desaprueba el bloque A.

| Fecha | Módulo | Prompt (resumen) | Qué se aceptó | Qué se corrigió a mano | Qué falló |
|---|---|---|---|---|---|
| 2026-11-19 | Kickoff / A | "Leé el pack de cátedra, armá la estructura del TP, corregí lo necesario y generá los datos" | Estructura de carpetas, `.env.example`, `.gitignore`, plantillas de ADR y de `01-discovery`, contrato Bronze con las 17 columnas reales del CSV | TODO: revisar | El `docker-compose.yml` del pack tenía mal los puertos internos de MySQL (3307) y Mongo (27018); la IA los detectó y corrigió. Falta probar `docker compose up` en la máquina del squad |
| 2026-11-19 | Todos (código) | "Hacé todo lo necesario para que el TP funcione con todos los datos" | Compose con Hadoop/Hive/HBase/Pig/Flume, imagen `tools`, `run.ps1`, scripts de M1–M14, ADR 001–006, contratos Silver/Gold, fichas 4 V. Probado en el entorno de la IA: perfilado, job Gold (1 M filas), streaming, limpieza Spark, prep del grafo | TODO: cada owner revisa su módulo y anota acá qué cambió | En las pruebas aparecieron y se corrigieron: (1) la API puede mandar enteros donde Spark espera double; (2) el `explain` con cache ocultaba la poda de particiones; (3) umbrales de alerta que disparaban en 69 de 77 ventanas; (4) pandas 3 guarda fechas en µs y rompía la ventana de 2 min; (5) Spark JDBC no acepta `query` con `partitionColumn`. Mongo/Cassandra/Neo4j/Hadoop no se pudieron probar en el entorno de la IA (sin Docker) |
| | | | | | |
