// M13 · Queries de negocio (squad 2002)

// 1) Amigos en común — pares con más amigos en común
MATCH (a:Rider)-[:AMIGO_DE]-(c:Rider)-[:AMIGO_DE]-(b:Rider)
WHERE a.rider_id < b.rider_id
RETURN a.rider_id AS rider_a, b.rider_id AS rider_b,
       count(DISTINCT c) AS amigos_en_comun, collect(DISTINCT c.rider_id) AS quienes
ORDER BY amigos_en_comun DESC, rider_a, rider_b
LIMIT 5;

// 1b) Amigos en común de un par concreto
MATCH (a:Rider {rider_id: 'R0045'})-[:AMIGO_DE]-(c:Rider)-[:AMIGO_DE]-(b:Rider {rider_id: 'R0075'})
RETURN a.rider_id AS rider_a, b.rider_id AS rider_b, collect(c.rider_id) AS amigos_en_comun;

// 2) Camino más corto entre 2 riders (amistad o viaje compartido)
MATCH p = shortestPath((a:Rider {rider_id: 'R0001'})-[:AMIGO_DE|VIAJO_CON*..10]-(b:Rider {rider_id: 'R0099'}))
RETURN [n IN nodes(p) | n.rider_id] AS camino,
       [r IN relationships(p) | type(r)] AS via,
       length(p) AS saltos;

// 3) Recomendación: riders que salen de las mismas estaciones y NO son amigos (ordenado por afinidad)
MATCH (a:Rider)-[:SALE_DE]->(e:Estacion)<-[:SALE_DE]-(b:Rider)
WHERE a.rider_id < b.rider_id AND NOT (a)-[:AMIGO_DE]-(b)
WITH a, b, collect(DISTINCT e.station_id) AS estaciones_en_comun
OPTIONAL MATCH (a)-[:LE_GUSTA]->(i:Interes)<-[:LE_GUSTA]-(b)
WITH a, b, estaciones_en_comun, collect(DISTINCT i.nombre) AS intereses_en_comun
RETURN a.rider_id AS rider, b.rider_id AS sugerencia, estaciones_en_comun, intereses_en_comun,
       size(estaciones_en_comun) * 2 + size(intereses_en_comun) AS afinidad
ORDER BY afinidad DESC, rider, sugerencia
LIMIT 10;

// 3b) Recomendación para un rider concreto
MATCH (a:Rider {rider_id: 'R0001'})-[:SALE_DE]->(e:Estacion)<-[:SALE_DE]-(b:Rider)
WHERE a <> b AND NOT (a)-[:AMIGO_DE]-(b)
OPTIONAL MATCH (a)-[:LE_GUSTA]->(i:Interes)<-[:LE_GUSTA]-(b)
RETURN b.rider_id AS sugerencia, collect(DISTINCT e.station_id) AS estaciones, collect(DISTINCT i.nombre) AS intereses,
       count(DISTINCT e) * 2 + count(DISTINCT i) AS afinidad
ORDER BY afinidad DESC, sugerencia
LIMIT 5;

// 4) Fraude / collusion A: 3 riders que arrancan viajes en la misma estación con < 2 min de diferencia,
//    mucho más seguido de lo esperable (los 3 pares del triángulo con z >= 2.5)
MATCH (a:Rider)-[x:INICIO_SINCRONIZADO]-(b:Rider)-[y:INICIO_SINCRONIZADO]-(c:Rider)-[z:INICIO_SINCRONIZADO]-(a)
WHERE a.rider_id < b.rider_id AND b.rider_id < c.rider_id
RETURN a.rider_id, b.rider_id, c.rider_id, [x.veces, y.veces, z.veces] AS co_inicios, [x.z, y.z, z.z] AS z
ORDER BY x.z + y.z + z.z DESC;

// 4b) Pares más sospechosos (sin triángulo): para revisar a mano
MATCH (a:Rider)-[s:INICIO_SINCRONIZADO]->(b:Rider)
RETURN a.rider_id AS rider_a, b.rider_id AS rider_b, s.veces AS co_inicios_2min, s.esperado AS esperado, s.z AS z,
       EXISTS { (a)-[:AMIGO_DE]-(b) } AS son_amigos
ORDER BY z DESC
LIMIT 5;

// 4c) Fraude / collusion B: triángulos de viajes compartidos declarados (VIAJO_CON)
MATCH (a:Rider)-[x:VIAJO_CON]-(b:Rider)-[y:VIAJO_CON]-(c:Rider)-[z:VIAJO_CON]-(a)
WHERE a.rider_id < b.rider_id AND b.rider_id < c.rider_id
RETURN a.rider_id, b.rider_id, c.rider_id, x.veces + y.veces + z.veces AS viajes_compartidos,
       x.estaciones + y.estaciones + z.estaciones AS estaciones
ORDER BY viajes_compartidos DESC;
