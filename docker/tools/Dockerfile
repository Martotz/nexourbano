# Imagen "tools": Python + Java 17 + PySpark 4 + drivers de todos los motores.
# Evita instalar Python/Java en Windows: todo el código del TP corre acá.
FROM python:3.12-slim-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends openjdk-17-jre-headless curl procps \
 && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    PYTHONUNBUFFERED=1 \
    CASS_DRIVER_NO_CYTHON=1

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Jars descargados en el build: los jobs no dependen de Maven en tiempo de ejecución.
ARG MVN=https://repo1.maven.org/maven2
RUN mkdir -p /opt/jars && cd /opt/jars \
 && curl -fsSLO $MVN/io/delta/delta-spark_2.13/4.0.0/delta-spark_2.13-4.0.0.jar \
 && curl -fsSLO $MVN/io/delta/delta-storage/4.0.0/delta-storage-4.0.0.jar \
 && curl -fsSLO $MVN/com/mysql/mysql-connector-j/9.1.0/mysql-connector-j-9.1.0.jar

WORKDIR /nexo
CMD ["sleep", "infinity"]
