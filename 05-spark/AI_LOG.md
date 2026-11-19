# Bitácora de IA — 05-spark (M8–M9)

Herramienta: Claude Opus 5.5 (claude.ai). Bitácora completa del squad: [`/AI_LOG.md`](../AI_LOG.md).

| Fecha | Prompt (resumen) | Qué se aceptó | Qué se corrigió | Qué falló |
|---|---|---|---|---|
| 2026-11-19 | Job Gold con joins, explain anotado y streaming con ventana 2 min / watermark 1 min | job_gold.py, stream_alertas.py, stream_replay.py | unpersist antes del explain; umbrales 7/8; lectura de recentProgress | El cache ocultaba la poda de particiones; umbrales iniciales disparaban 69 de 77 ventanas |
| | | | _(completar: qué revisó o cambió a mano el owner del módulo)_ | |
