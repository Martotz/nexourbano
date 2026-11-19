# Quiz interno de 4 V (M4) — actividad de squad

Cargar estas 8 preguntas en Kahoot, Mentimeter o Google Forms, jugarlo entre los 3 y exportar el ranking a
`04-hadoop/quiz.csv` (columnas: `participante,puntaje,correctas,tiempo_promedio_s`). **No completar el CSV a mano.**

1. ¿Qué V obliga a usar watermark en el streaming de NexoUrbano? — a) Volumen b) **Velocidad** c) Variedad d) Valor
2. 1 M de viajes en 90 días son ~160 MB. ¿Cuántos bloques ocupa en HDFS con bloque de 128 MB? — a) 1 b) **2** c) 3 d) 160
3. ¿Qué motor elegimos para "última lectura de cada vehículo"? — a) Hive b) MongoDB c) **Cassandra** d) Neo4j
4. ¿Qué pasa con los datos al hacer DROP de una tabla **externa** de Hive? — a) se borran b) **quedan en HDFS** c) pasan a la papelera d) se vuelven internos
5. Un evento llega 5 min tarde con watermark de 1 min y ventana de 2 min. — a) se cuenta b) **se descarta** c) abre otra ventana d) frena el stream
6. ¿Qué riesgo de veracidad mitiga la regla `duration_s < 30`? — a) bots en redes b) **viajes que no ocurrieron / desbloqueos fallidos** c) drift de GPS d) duplicados
7. El catálogo con precio por ciudad en SQL necesita 3 joins. En Mongo es… — a) 3 lookups b) **un documento** c) un índice d) una vista
8. ¿Por qué la rowkey de HBase lleva un prefijo de bucket? — a) para ordenar por fecha b) **para evitar hotspot con IDs secuenciales** c) por compresión d) por seguridad
