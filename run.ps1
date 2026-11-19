<#
.SYNOPSIS
  Orquestador del TP NexoUrbano (squad 2002). Cada paso deja su log en evidence\.

.EXAMPLE
  .\run.ps1 setup      # .env, imágenes, datos (1 M viajes), servicios base
  .\run.ps1 s1         # M1–M3: EcoBici + perfilado + ingesta API + Data Lake (MinIO; Azure si hay credenciales)
  .\run.ps1 s2         # M4–M7: Hadoop (HDFS, MapReduce, HBase, Hive, Pig, JDBC, Flume)
  .\run.ps1 s3         # M8–M9: Spark batch Gold + Structured Streaming
  .\run.ps1 s4         # M10–M14: Mongo, Cassandra, Neo4j y producto
  .\run.ps1 all        # todo en orden
  .\run.ps1 s2.hive    # un solo paso (ver la lista con .\run.ps1 help)
  .\run.ps1 status | down
#>
param([Parameter(Position = 0)][string]$Paso = "help")

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$PROFILES = @("--profile", "hadoop", "--profile", "cassandra", "--profile", "neo4j")

function Titulo($t) { Write-Host "`n==== $t ====" -ForegroundColor Cyan }

function DC {
    # docker compose con todos los perfiles visibles (para poder referenciar cualquier servicio).
    # La salida pasa por el pipeline para que Start-Transcript la registre; docker escribe progreso en
    # stderr, así que acá no se corta por eso: se mira el código de salida.
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    & docker compose @PROFILES @args 2>&1 | ForEach-Object { Write-Host "$_" }
    $code = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($code -ne 0) { throw "docker compose $($args -join ' ') terminó con código $code" }
}

function EnTools([string]$cmd, [string]$log) {
    # Corre un comando en el contenedor tools y guarda la salida en evidence/<log>
    $dir = Split-Path "evidence/$log" -Parent
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    DC exec -T tools bash -c "set -o pipefail; $cmd 2>&1 | grep -v -E '^(WARNING|SLF4J)|log4j|NativeCodeLoader' | tee /nexo/evidence/$log"
}

function EnServicio([string]$svc, [string]$script) { DC exec -T $svc bash "/nexo/$script" }

function Esperar([string[]]$servicios) { DC up -d --wait @servicios }

# ----------------------------------------------------------------------------- pasos
function Setup {
    Titulo "Docker"
    $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    docker info --format "Docker {{.ServerVersion}} - {{.NCPU}} CPU - {{.MemTotal}} bytes de RAM para contenedores" 2>&1 | ForEach-Object { Write-Host "$_" }
    $code = $LASTEXITCODE; $ErrorActionPreference = $prev
    if ($code -ne 0) { throw "Docker Desktop no está corriendo." }

    if (-not (Test-Path .env)) {
        Titulo "Creando .env con contraseñas aleatorias (no se commitea)"
        function Clave { -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 20 | ForEach-Object { [char]$_ }) }
        (Get-Content .env.example) `
            -replace '^MYSQL_ROOT_PASSWORD=.*', "MYSQL_ROOT_PASSWORD=$(Clave)" `
            -replace '^NEO4J_PASSWORD=.*', "NEO4J_PASSWORD=$(Clave)" `
            -replace '^MINIO_ROOT_PASSWORD=.*', "MINIO_ROOT_PASSWORD=$(Clave)" |
            Set-Content -Encoding ascii .env
    }

    Titulo "Construyendo la imagen tools (la primera vez tarda ~10 min)"
    DC build tools

    Titulo "Servicios base"
    Esperar @("mysql", "mongo", "minio", "tools")
    DC up minio-init

    # 1 M viajes pesan ~160 MB; si falta o es la versión chica (250 k), se regenera (misma semilla = mismos datos)
    if (-not (Test-Path data/viajes.csv) -or (Get-Item data/viajes.csv).Length -lt 100MB) {
        Titulo "Generando datos (seed 2002, 1 M viajes)"
        EnTools "python tools/generar_datos.py --seed 2002 --n-viajes 1000000 --out data" "setup/generar_datos.log"
        $prev = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        git checkout -- data/MANIFIESTO.txt 2>&1 | Out-Null   # solo cambia la fecha de generación
        $ErrorActionPreference = $prev
    }
    DC ps
}

function S1-EcoBici { Titulo "M1 · Dataset abierto EcoBici"; EnTools "python 01-discovery/descargar_ecobici.py" "s1/descarga_ecobici.log" }
function S1-Perfilado {
    Titulo "M1 · Perfilado"
    EnTools "python 01-discovery/perfilado.py --dataset sintetico" "s1/perfilado_sintetico.log"
    EnTools "python 01-discovery/perfilado.py --dataset ecobici" "s1/perfilado_ecobici.log"
}
function S1-Ingesta { Titulo "M3 · Ingesta Open-Meteo + Mastodon (versión local del notebook)"; EnTools "python 03-databricks/01_ingesta.py" "s1/ingesta_local.log" }
function S1-Lake {
    Titulo "M2 · Data Lake (MinIO; Azure si .env tiene AZURE_STORAGE_ACCOUNT)"
    $dest = if ((Get-Content .env | Select-String '^AZURE_STORAGE_ACCOUNT=.+')) { "ambos" } else { "minio" }
    EnTools "python 02-azure-datalake/subir_bronze.py --destino $dest" "s1/datalake.log"
}

function Build-Hadoop {
    Titulo "Construyendo la imagen hadoop-edge (Pig + Flume)"
    DC build hadoop-edge
}

function S2-Up {
    Build-Hadoop
    Titulo "Levantando Hadoop (namenode, datanode, yarn, edge, hive, hbase)"
    DC up -d namenode datanode resourcemanager nodemanager hadoop-edge hive hbase
}
function S2-Bootstrap { Titulo "M4 · Bootstrap"; EnServicio hadoop-edge "04-hadoop/bootstrap.sh" }
function S2-Hdfs { Titulo "M5 · HDFS"; EnServicio hadoop-edge "04-hadoop/hdfs/hdfs_nexo.sh" }
function S2-WordCount { Titulo "M5 · WordCount"; EnServicio hadoop-edge "04-hadoop/mapreduce/wordcount.sh" }
function S2-HBase {
    Titulo "M6 · HBase"
    EnTools "python 04-hadoop/hbase/gen_hbase_script.py" "hadoop/hbase_gen.log"
    EnServicio hbase "04-hadoop/hbase/hbase_run.sh"
}
function S2-Hive { Titulo "M6 · Hive"; EnServicio hive "04-hadoop/hive/hive_run.sh" }
function S2-Pig { Titulo "M7 · Pig"; EnServicio hadoop-edge "04-hadoop/pig/pig_run.sh" }
function S2-Jdbc { Titulo "M7 · Sqoop plan B: Spark JDBC"; EnTools "python 04-hadoop/sqoop/riders_jdbc.py" "hadoop/riders_jdbc.log" }
function S2-Flume { Titulo "M7 · Flume"; EnServicio hadoop-edge "04-hadoop/flume/flume_run.sh" }

function S3-Gold {
    Titulo "M8 · Spark batch Gold"
    EnTools "python 05-spark/batch/job_gold.py" "spark/job_gold.log"
    EnTools "python 04-hadoop/pig/clean_viajes_spark.py" "spark/clean_viajes_spark.log"
}
function S3-Stream { Titulo "M9 · Structured Streaming (≈ 3 min)"; EnTools "python 05-spark/streaming/stream_alertas.py --duracion 240" "spark/streaming.log" }

function S4-Up {
    Titulo "Liberando RAM: se apaga Hadoop (S4 usa sus resultados ya guardados)"
    DC stop namenode datanode resourcemanager nodemanager hadoop-edge hive hbase
    Titulo "Levantando Cassandra y Neo4j"
    Esperar @("mongo", "cassandra", "neo4j", "tools")
}
function S4-Mongo { Titulo "M10–M11 · MongoDB"; EnServicio mongo "06-mongodb/mongo_run.sh" }
function S4-Cassandra { Titulo "M12 · Cassandra"; EnServicio cassandra "07-cassandra/cassandra_run.sh" }
function S4-Neo4j {
    Titulo "M13 · Neo4j"
    EnTools "python 08-neo4j/prep_grafo.py" "neo4j/prep_grafo.log"
    EnServicio neo4j "08-neo4j/neo4j_run.sh"
}
function S4-Producto { Titulo "M14 · Producto: 5 preguntas"; EnTools "python 09-producto/decision_ops.py" "producto/decision_ops.log" }

$PASOS = [ordered]@{
    "setup"       = { Setup }
    "build.hadoop" = { Build-Hadoop }
    "s1.ecobici"  = { S1-EcoBici }; "s1.perfilado" = { S1-Perfilado }; "s1.ingesta" = { S1-Ingesta }; "s1.lake" = { S1-Lake }
    "s2.up"       = { S2-Up }; "s2.bootstrap" = { S2-Bootstrap }; "s2.hdfs" = { S2-Hdfs }; "s2.wordcount" = { S2-WordCount }
    "s2.hbase"    = { S2-HBase }; "s2.hive" = { S2-Hive }; "s2.pig" = { S2-Pig }; "s2.jdbc" = { S2-Jdbc }; "s2.flume" = { S2-Flume }
    "s3.gold"     = { S3-Gold }; "s3.stream" = { S3-Stream }
    "s4.up"       = { S4-Up }; "s4.mongo" = { S4-Mongo }; "s4.cassandra" = { S4-Cassandra }; "s4.neo4j" = { S4-Neo4j }; "s4.producto" = { S4-Producto }
}

function Correr([string]$prefijo) {
    foreach ($k in $PASOS.Keys) { if ($k.StartsWith("$prefijo.")) { & $PASOS[$k] } }
}

$inicio = Get-Date
switch ($Paso) {
    "help" { Get-Help $PSCommandPath -Examples; "Pasos:"; $PASOS.Keys | ForEach-Object { "  $_" } }
    "status" { DC ps }
    "down" { DC down }
    "all" { Setup; Correr "s1"; Correr "s2"; Correr "s3"; Correr "s4" }
    { $_ -in "s1", "s2", "s3", "s4" } { Correr $Paso }
    default {
        if ($PASOS.Contains($Paso)) { & $PASOS[$Paso] } else { throw "Paso desconocido: $Paso (ver .\run.ps1 help)" }
    }
}
Write-Host ("`nOK '{0}' en {1:mm\:ss}" -f $Paso, ((Get-Date) - $inicio)) -ForegroundColor Green
