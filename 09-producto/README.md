# M14 · Producto Gold

`.\run.ps1 s4.producto` → `python 09-producto/decision_ops.py` → `decision_ops.md` (reporte) + `evidence/producto/decision_ops.log`.

| Pregunta | Motores |
|---|---|
| P1 ¿Dónde reponer en las próximas 3 h si llueve? | Spark Gold (`gold_demanda_estacion_hora`) + Open-Meteo forecast |
| P2 ¿Qué vehículo retirar hoy? | Cassandra (`PER PARTITION LIMIT 1`) + SOH de la flota |
| P3 ¿Qué pase venderle a un rider? | MongoDB (ventas + `$lookup` catálogo) + Neo4j (intereses, amigos) |
| P4 ¿Hay collusion / fraude social? | Neo4j |
| P5 ¿Facturación vs. tickets "cobro"? | Spark Gold (+ Hive) + WordCount MapReduce |

`ventas_agg.json` lo genera `06-mongodb/agg_ventas.js`. Si una fuente no responde, el reporte dice qué dato faltó.
