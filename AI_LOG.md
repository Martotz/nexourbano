# Bitácora de IA — NexoUrbano

Squad: 2002
Herramientas usadas (versiones): Claude (Opus 5.5)

Regla: una fila por sesión relevante. Mentir acá desaprueba el bloque A.

| Fecha | Módulo | Prompt (resumen) | Qué se aceptó | Qué se corrigió a mano | Qué falló |
|---|---|---|---|---|---|
| 2026-11-19 | Kickoff / A | "Leé el pack de cátedra, armá la estructura del TP, corregí lo necesario y generá los datos" | Estructura de carpetas, `.env.example`, `.gitignore`, plantillas de ADR y de `01-discovery`, contrato Bronze con las 17 columnas reales del CSV | TODO: revisar | El `docker-compose.yml` del pack tenía mal los puertos internos de MySQL (3307) y Mongo (27018); la IA los detectó y corrigió. Falta probar `docker compose up` en la máquina del squad |
