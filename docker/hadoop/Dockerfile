# Nodo "edge" de Hadoop: cliente HDFS/YARN + Pig + Flume.
# Las descargas van en una etapa aparte para no depender de las herramientas de la imagen base.
# Primero el CDN de Apache (rápido); si la versión ya no está ahí, archive.apache.org (lento, limitado).
FROM alpine:3.20 AS dl
ARG PIG_VERSION=0.17.0
ARG FLUME_VERSION=1.11.0
RUN apk add --no-cache curl tar \
 && bajar() { for base in https://dlcdn.apache.org https://downloads.apache.org https://archive.apache.org/dist; do \
        echo "probando $base/$1"; curl -fSL --connect-timeout 15 -o /tmp/pkg.tgz "$base/$1" && return 0; done; return 1; } \
 && bajar pig/pig-${PIG_VERSION}/pig-${PIG_VERSION}.tar.gz && tar xzf /tmp/pkg.tgz -C /opt && mv /opt/pig-${PIG_VERSION} /opt/pig \
 && bajar flume/${FLUME_VERSION}/apache-flume-${FLUME_VERSION}-bin.tar.gz && tar xzf /tmp/pkg.tgz -C /opt \
 && mv /opt/apache-flume-${FLUME_VERSION}-bin /opt/flume \
 # guava 11 de Flume choca con la de Hadoop 3 (NoSuchMethodError en el sink HDFS)
 && rm -f /opt/flume/lib/guava-*.jar /tmp/pkg.tgz

FROM apache/hadoop:3.3.6
COPY --from=dl /opt/pig /opt/pig
COPY --from=dl /opt/flume /opt/flume
ENV PIG_HOME=/opt/pig \
    FLUME_HOME=/opt/flume \
    PATH=$PATH:/opt/pig/bin:/opt/flume/bin
CMD ["sleep", "infinity"]
