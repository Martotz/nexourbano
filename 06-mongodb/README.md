# M10–M11 · MongoDB: catálogo comercial y analítica

`docker compose exec -T mongo bash /nexo/06-mongodb/mongo_run.sh` (o `.\run.ps1 s4.mongo`)

| Archivo | Qué hace |
|---|---|
| `crud.js` | Carga 40 productos (precio, stock y ficha anidados) y 4 000 ventas; `insertMany`, `find`, `updateOne`, `deleteOne` del SKU discontinuado; índices medidos con `explain("executionStats")` antes y después |
| `indices_explain.json` | Resultado de la medición (lo escribe `crud.js`) |
| `agg_ventas.js` | Pipeline: `$match` último trimestre → `$facet` (total por categoría, top 5 + `$lookup` a productos, ventas por mes) → `$project` → `09-producto/ventas_agg.json`. Extra: `$geoNear` con índice `2dsphere` |
| `pipeline_ventas.json` | El pipeline tal cual se ejecutó |

## SQL vs. documento (8 líneas)
1. En SQL el producto se normaliza en 4 tablas: `producto`, `producto_precio(sku, ciudad, precio)`, `producto_stock(sku, ciudad, stock)`, `producto_tag(sku, tag)`.
2. "Pases con tag *lluvia*, su precio y stock en Buenos Aires" pide **3 joins** (precio, stock y tag) más un filtro por ciudad en dos de ellos.
3. En Mongo es **un documento**: `find({categoria: "pase", tags: "lluvia"}, {"precios.Buenos Aires": 1, "stock.Buenos Aires": 1})`.
4. El catálogo se lee mucho más de lo que se escribe y siempre se lee entero: el documento coincide con la unidad de lectura.
5. Sumar una ciudad nueva (Rosario) es agregar una clave en `precios` y `stock`, sin `ALTER TABLE` ni migración.
6. El índice multikey en `tags` indexa cada elemento del array: el filtro por tag no recorre la colección.
7. Lo que se pierde: integridad referencial; una venta puede apuntar a un SKU borrado (por eso `$lookup` con `preserveNullAndEmptyArrays`).
8. Por eso las **ventas** (hechos, alto volumen, agregaciones) también se analizan en Spark; Mongo sirve el catálogo y la analítica comercial liviana.
