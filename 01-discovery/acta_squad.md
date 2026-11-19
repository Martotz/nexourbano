# Acta de squad — ¿qué V es la más cara de mentir en NexoUrbano?

> **Borrador para discutir.** Lo redactó la IA con los números del perfilado; el squad lo debate,
> lo corrige y deja abajo fecha, asistentes y conclusión final. Registrarlo en AI_LOG.md.

- Fecha: ____ · Asistentes: Gabriel Donoso, Julián Spinedi, Agustín Martínez

1. Propuesta: la más cara de mentir es la **Veracidad**, porque se cobra plata por cada viaje.
2. Un viaje de 8 s o de 5,5 h en Bronze factura: el perfilado encontró 2,02 % de viajes absurdos (20 182 de 1 M).
3. Si entran a Gold, inflan la facturación y la demanda que usa ops para reponer scooters.
4. Un evento tardío mal contado dispara o tapa una alerta de fraude (payment_fail).
5. El ticket más frecuente después de rueda/candado es **#cobro** (doble cobro): la veracidad ya le cuesta soporte.
6. Velocidad mal resuelta cuesta minutos; volumen mal resuelto cuesta hardware; veracidad mal resuelta cuesta confianza y reintegros.
7. Contrapropuesta a discutir: Velocidad, porque una flota caída sin alerta deja riders sin vehículo.
8. Control 1: contrato YAML con reglas de rechazo; Spark separa los rechazos con motivo (`silver_viajes_rechazos`).
9. Control 2: umbral `rechazo_max_pct: 3` en el contrato; si se supera, no se publica Gold.
10. Control 3: watermark de 1 min en streaming y descarte medido (`numRowsDroppedByWatermark`).
11. Control 4: `dropDuplicates` por clave en Silver (0 duplicados de `ride_id` medidos).
12. Control 5: perfilado versionado en `01-discovery/perfilado/`: cada corrida deja su JSON para comparar drift.
13. Riesgo abierto: el dataset sintético no tiene estacionalidad horaria ni efecto lluvia; se contrasta con EcoBici.
14. Decisión del squad: ______________________________________________
15. Responsable del control: ______________________________________________
