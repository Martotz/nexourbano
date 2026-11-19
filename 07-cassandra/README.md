# M12 · Cassandra

Estado: pendiente

## Entregables

- [ ] schema.cql — keyspace `nexo` RF=1, tabla `lecturas_vehiculo` (PK vehicle_id, clustering ts DESC)
- [ ] queries.cql — últimas 20, rango horario, query que falla por no respetar la PK
- [ ] Carga: `COPY ... FROM '/import/lecturas_sensores.csv'`
- [ ] ONE vs. QUORUM en `ADR/006-cassandra-consistencia.md`
