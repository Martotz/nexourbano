# ADR 006 — Consistencia en Cassandra: batería en vivo vs. facturación

- Estado: aceptada · Módulo: M12 · Fecha: 2026-11-19

## Contexto
Sandbox: 1 nodo, keyspace `nexo` con `SimpleStrategy`, **RF = 1**. Producción: `NetworkTopologyStrategy`, **RF = 3** por datacenter.
Con RF=1, ONE y QUORUM leen la misma única réplica (ver `queries.cql`); la diferencia aparece con RF=3.

## Decisión (RF = 3)
| Caso | Escritura | Lectura | Por qué |
|---|---|---|---|
| **Batería en vivo** (`lecturas_vehiculo`) | ONE | ONE | Llega una lectura cada pocos segundos: si una réplica está atrasada, la próxima la corrige. Prima latencia y disponibilidad: el mapa de flota no puede caerse porque un nodo esté lento |
| **Facturación** (cobros, saldos) | QUORUM | QUORUM | QUORUM + QUORUM = 2 + 2 > 3: toda lectura ve la última escritura confirmada. Un saldo leído de una réplica vieja cobra dos veces (justo el ticket #cobro más frecuente del WordCount) |

## Consecuencias
Con RF=3 y QUORUM, la facturación tolera 1 nodo caído; con ONE, la telemetría tolera 2. Si cae un datacenter entero,
la facturación debería usar LOCAL_QUORUM para no depender de la latencia entre regiones.
