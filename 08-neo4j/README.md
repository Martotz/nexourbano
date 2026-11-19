# M13 · Neo4j: grafo social y recomendaciones

`.\run.ps1 s4.neo4j` → `prep_grafo.py` (CSV en `data/derived/`) + `grafo.cypher` (carga) + `queries.cypher`. Log: `evidence/neo4j/neo4j.log`.
Browser: http://localhost:7474 (usuario `neo4j`, contraseña `NEO4J_PASSWORD` de `.env`). Captura del grafo → `evidence/neo4j/`.

| Nodos | Relaciones |
|---|---|
| `Rider` (120), `Estacion` (24), `Interes` (10) | `AMIGO_DE` (220), `VIAJO_CON` (160), `LE_GUSTA` (229), `SALE_DE` (top 3 estaciones de cada rider, sacado de 1 M viajes), `INICIO_SINCRONIZADO` (pares que arrancan en la misma estación con < 2 min mucho más de lo esperable) |

Queries: amigos en común · camino más corto · recomendación (mismas estaciones, no amigos, intereses en común) · fraude (triángulos de inicios sincronizados y de viajes compartidos).

**Resultado esperado (verificado con networkx sobre los mismos CSV):** R0045–R0075 con 3 amigos en común; camino R0001 → R0055 → R0099;
0 triángulos de inicio sincronizado (no hay collusion de 3 en los datos sintéticos) y 2 triángulos `VIAJO_CON` (R0092–R0104–R0113 y R0021–R0093–R0104).

Para la captura en Browser: `MATCH p=(r:Rider {rider_id:'R0104'})-[*1..2]-() RETURN p LIMIT 80`
