// M10 · MongoDB: catálogo comercial NexoUrbano (squad 2002)
//   docker compose exec -T mongo bash /nexo/06-mongodb/mongo_run.sh
// Carga productos (documentos anidados) y ventas desde /nexo/data, hace CRUD y mide un índice.
const fs = require("fs");
db = db.getSiblingDB("nexo");
const titulo = (t) => print(`\n========== ${t} ==========`);

// ---------------------------------------------------------------- carga
titulo("Carga");
db.productos.drop();
db.ventas.drop();
const productos = JSON.parse(fs.readFileSync("/nexo/data/productos.json", "utf8")).map((p) => ({
  ...p,
  // anidado: precio y stock por ciudad + ficha comercial
  ficha: {
    descripcion: `${p.nombre} NexoUrbano`,
    vigencia_dias: p.categoria === "pase" ? 30 : null,
    canales: ["app", "web", "estacion"],
  },
  actualizado: new Date("2026-06-01T00:00:00Z"),
}));
const r = db.productos.insertMany(productos);
print(`insertMany productos: ${Object.keys(r.insertedIds).length} documentos`);

const [cab, ...filas] = fs.readFileSync("/nexo/data/ventas.csv", "utf8").trim().split(/\r?\n/);
const cols = cab.split(",");
const ventas = filas.map((l) => {
  const v = Object.fromEntries(l.split(",").map((x, i) => [cols[i], x]));
  return { ...v, ts: new Date(v.ts), monto_ars: Number(v.monto_ars) };
});
db.ventas.insertMany(ventas);
print(`insertMany ventas: ${db.ventas.countDocuments()} documentos`);
printjson(db.productos.findOne({ sku: "SKU001" }));

// ---------------------------------------------------------------- read
titulo("find: pases con precio en Buenos Aires <= 5990, activos");
db.productos
  .find(
    { categoria: "pase", activo: true, "precios.Buenos Aires": { $lte: 5990 } },
    { _id: 0, sku: 1, nombre: 1, "precios.Buenos Aires": 1, tags: 1, "stock.Buenos Aires": 1 }
  )
  .sort({ "precios.Buenos Aires": 1 })
  .forEach((d) => printjson(d));

// ---------------------------------------------------------------- update
titulo("updateOne: ajuste de precio de SKU001 (+12 % en Buenos Aires)");
const antes = db.productos.findOne({ sku: "SKU001" }, { _id: 0, sku: 1, precios: 1, actualizado: 1 });
printjson({ antes });
const nuevo = Math.round(antes.precios["Buenos Aires"] * 1.12);
printjson(
  db.productos.updateOne(
    { sku: "SKU001" },
    { $set: { "precios.Buenos Aires": nuevo }, $currentDate: { actualizado: true } }
  )
);
printjson({ despues: db.productos.findOne({ sku: "SKU001" }, { _id: 0, sku: 1, precios: 1, actualizado: 1 }) });

// ---------------------------------------------------------------- delete
titulo("deleteOne: SKU discontinuado (activo = false)");
const disc = db.productos.find({ activo: false }, { _id: 0, sku: 1, nombre: 1 }).toArray();
printjson(disc);
printjson(db.productos.deleteOne({ sku: disc[0].sku, activo: false }));
print(`productos restantes: ${db.productos.countDocuments()}`);

// ---------------------------------------------------------------- índices medidos
const medir = (col, filtro, etiqueta) => {
  const e = db[col].find(filtro).explain("executionStats");
  const s = e.executionStats;
  const etapa = (p) => (p.inputStage ? `${p.stage} <- ${etapa(p.inputStage)}` : p.stage);
  const fila = {
    etiqueta,
    coleccion: col,
    filtro: JSON.stringify(filtro),
    plan: etapa(e.queryPlanner.winningPlan),
    nReturned: s.nReturned,
    totalDocsExamined: s.totalDocsExamined,
    totalKeysExamined: s.totalKeysExamined,
    executionTimeMillis: s.executionTimeMillis,
  };
  printjson(fila);
  return fila;
};

titulo("Índice multikey en tags (productos)");
db.productos.dropIndexes();
const q1 = { tags: "lluvia", activo: true };
const a1 = medir("productos", q1, "ANTES (sin índice)");
db.productos.createIndex({ tags: 1 });
const d1 = medir("productos", q1, "DESPUÉS (índice tags_1)");

titulo("Índice compuesto ciudad + categoria (ventas, 4 000 docs)");
db.ventas.dropIndexes();
const q2 = { ciudad: "Buenos Aires", categoria: "pase" };
const a2 = medir("ventas", q2, "ANTES (sin índice)");
db.ventas.createIndex({ ciudad: 1, categoria: 1 });
const d2 = medir("ventas", q2, "DESPUÉS (índice ciudad_1_categoria_1)");

const resumen = [a1, d1, a2, d2];
fs.writeFileSync("/nexo/06-mongodb/indices_explain.json", JSON.stringify(resumen, null, 2));
titulo("Resumen (también en 06-mongodb/indices_explain.json)");
resumen.forEach((x) =>
  print(`${x.coleccion.padEnd(9)} ${x.etiqueta.padEnd(38)} ${x.plan.padEnd(22)} docs=${String(x.totalDocsExamined).padStart(5)} keys=${String(x.totalKeysExamined).padStart(5)} n=${String(x.nReturned).padStart(4)} ms=${x.executionTimeMillis}`)
);
