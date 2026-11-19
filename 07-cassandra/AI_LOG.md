# Bitácora de IA — 07-cassandra (M12)

Herramienta: Claude Opus 5.5 (claude.ai). Bitácora completa del squad: [`/AI_LOG.md`](../AI_LOG.md).

| Fecha | Prompt (resumen) | Qué se aceptó | Qué se corrigió | Qué falló |
|---|---|---|---|---|
| 2026-11-19 | Tabla por query (vehicle_id, ts DESC), carga y anti-patrones | schema.cql, load.cql, queries.cql | DESCRIBE en una llamada aparte | DESCRIBE antes de refrescar el esquema no mostraba la tabla |
| | | | _(completar: qué revisó o cambió a mano el owner del módulo)_ | |
