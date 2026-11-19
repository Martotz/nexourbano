// M11 · MongoDB: analítica comercial con aggregation pipeline (squad 2002)
// Requiere crud.js (carga productos y ventas). Exporta 09-producto/ventas_agg.json
const fs = require("fs");
db = db.getSiblingDB("nexo");

const max = db.ventas.find().sort({ ts: -1 }).limit(1).next().ts;
const desde = new Date(max.getTime() - 90 * 24 * 3600 * 1000);
print(`Último trimestre sintético: ${desde.toISOString()} -> ${max.toISOString()}`);

const pipeline = [
  // 1) último trimestre
  { $match: { ts: { $gte: desde, $lte: max } } },
  {
    $facet: {
      // 2) total por categoría
      por_categoria: [
        { $group: { _id: "$categoria", ventas: { $sum: 1 }, revenue_ars: { $sum: "$monto_ars" } } },
        { $sort: { revenue_ars: -1 } },
      ],
      // 3) top 5 productos + 5) $lookup al catálogo
      top5_productos: [
        { $group: { _id: "$sku", ventas: { $sum: 1 }, revenue_ars: { $sum: "$monto_ars" } } },
        { $sort: { revenue_ars: -1 } },
        { $limit: 5 },
        { $lookup: { from: "productos", localField: "_id", foreignField: "sku", as: "producto" } },
        { $unwind: { path: "$producto", preserveNullAndEmptyArrays: true } },
      ],
      // 4) ventas por mes
      por_mes: [
        { $group: { _id: { $dateToString: { format: "%Y-%m", date: "$ts" } }, ventas: { $sum: 1 }, revenue_ars: { $sum: "$monto_ars" } } },
        { $sort: { _id: 1 } },
      ],
      por_canal: [{ $group: { _id: "$canal", ventas: { $sum: 1 } } }, { $sort: { ventas: -1 } }],
    },
  },
  // 6) documento de salida limpio
  {
    $project: {
      _id: 0,
      periodo: { desde: desde, hasta: max },
      por_categoria: {
        $map: { input: "$por_categoria", as: "c", in: { categoria: "$$c._id", ventas: "$$c.ventas", revenue_ars: "$$c.revenue_ars" } },
      },
      top5_productos: {
        $map: {
          input: "$top5_productos",
          as: "p",
          in: {
            sku: "$$p._id",
            nombre: "$$p.producto.nombre",
            categoria: "$$p.producto.categoria",
            tags: "$$p.producto.tags",
            ventas: "$$p.ventas",
            revenue_ars: "$$p.revenue_ars",
          },
        },
      },
      por_mes: { $map: { input: "$por_mes", as: "m", in: { mes: "$$m._id", ventas: "$$m.ventas", revenue_ars: "$$m.revenue_ars" } } },
      por_canal: { $map: { input: "$por_canal", as: "c", in: { canal: "$$c._id", ventas: "$$c.ventas" } } },
    },
  },
];

fs.writeFileSync("/nexo/06-mongodb/pipeline_ventas.json", JSON.stringify(pipeline, null, 2));
const out = db.ventas.aggregate(pipeline).toArray()[0];
// 7) export Gold
fs.writeFileSync("/nexo/09-producto/ventas_agg.json", EJSON.stringify(out, null, 2, { relaxed: true }));
printjson(out);
print("\nOK -> 09-producto/ventas_agg.json");

// Extra (geoespacial): estaciones a menos de 3 km del Obelisco
print("\n========== Extra 2dsphere: estaciones a < 3 km del Obelisco ==========");
db.estaciones.drop();
const [h, ...ls] = fs.readFileSync("/nexo/data/estaciones.csv", "utf8").trim().split(/\r?\n/);
const k = h.split(",");
db.estaciones.insertMany(
  ls.map((l) => {
    const e = Object.fromEntries(l.split(",").map((x, i) => [k[i], x]));
    return { _id: e.station_id, nombre: e.nombre, barrio: e.barrio, capacidad: Number(e.capacidad),
             ubicacion: { type: "Point", coordinates: [Number(e.lon), Number(e.lat)] } };
  })
);
db.estaciones.createIndex({ ubicacion: "2dsphere" });
db.estaciones
  .aggregate([
    { $geoNear: { near: { type: "Point", coordinates: [-58.3816, -34.6037] }, distanceField: "distancia_m",
                  maxDistance: 3000, spherical: true } },
    { $project: { nombre: 1, barrio: 1, capacidad: 1, distancia_m: { $round: ["$distancia_m", 0] } } },
  ])
  .forEach((d) => printjson(d));
