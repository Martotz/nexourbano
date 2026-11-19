// M13 · Neo4j: carga del grafo social de NexoUrbano (squad 2002)
// Archivos en /var/lib/neo4j/import = ./data del repo (derived/ lo genera 08-neo4j/prep_grafo.py)

MATCH (n) DETACH DELETE n;

CREATE CONSTRAINT rider_id IF NOT EXISTS FOR (r:Rider) REQUIRE r.rider_id IS UNIQUE;
CREATE CONSTRAINT estacion_id IF NOT EXISTS FOR (e:Estacion) REQUIRE e.station_id IS UNIQUE;
CREATE CONSTRAINT interes_nombre IF NOT EXISTS FOR (i:Interes) REQUIRE i.nombre IS UNIQUE;

// Nodos
LOAD CSV WITH HEADERS FROM 'file:///riders.csv' AS row
MERGE (r:Rider {rider_id: row.rider_id})
SET r.nombre = row.nombre, r.plan = row.plan, r.alta = date(row.alta);

LOAD CSV WITH HEADERS FROM 'file:///estaciones.csv' AS row
MERGE (e:Estacion {station_id: row.station_id})
SET e.nombre = row.nombre, e.barrio = row.barrio, e.capacidad = toInteger(row.capacidad),
    e.ubicacion = point({latitude: toFloat(row.lat), longitude: toFloat(row.lon)});

// Relaciones
LOAD CSV WITH HEADERS FROM 'file:///derived/amigos.csv' AS row
MATCH (a:Rider {rider_id: row.a}), (b:Rider {rider_id: row.b})
MERGE (a)-[:AMIGO_DE]->(b);

LOAD CSV WITH HEADERS FROM 'file:///derived/viajo_con.csv' AS row
MATCH (a:Rider {rider_id: row.a}), (b:Rider {rider_id: row.b})
MERGE (a)-[v:VIAJO_CON]->(b)
SET v.veces = coalesce(v.veces, 0) + toInteger(row.n),
    v.estaciones = coalesce(v.estaciones, []) + row.station_id;

LOAD CSV WITH HEADERS FROM 'file:///derived/le_gusta.csv' AS row
MATCH (r:Rider {rider_id: row.rider_id})
MERGE (i:Interes {nombre: row.interes})
MERGE (r)-[:LE_GUSTA]->(i);

LOAD CSV WITH HEADERS FROM 'file:///derived/sale_de.csv' AS row
MATCH (r:Rider {rider_id: row.rider_id}), (e:Estacion {station_id: row.station_id})
MERGE (r)-[s:SALE_DE]->(e)
SET s.viajes = toInteger(row.viajes);

LOAD CSV WITH HEADERS FROM 'file:///derived/inicio_sincronizado.csv' AS row
MATCH (a:Rider {rider_id: row.a}), (b:Rider {rider_id: row.b})
MERGE (a)-[s:INICIO_SINCRONIZADO]->(b)
SET s.veces = toInteger(row.veces), s.esperado = toFloat(row.esperado), s.z = toFloat(row.z);

// Resumen de la carga
MATCH (n) RETURN labels(n)[0] AS nodo, count(*) AS cantidad ORDER BY nodo;
MATCH ()-[r]->() RETURN type(r) AS relacion, count(*) AS cantidad ORDER BY relacion;
