# Nodo "edge" de Hadoop: cliente HDFS/YARN + Pig + Flume.
# Las descargas se hacen en una etapa aparte para no depender de las herramientas de la imagen base.
FROM alpine:3.20 AS dl
ARG PIG_VERSION=0.17.0
ARG FLUME_VERSION=1.11.0
RUN apk add --no-cache curl tar \
 && curl -fsSL https://archive.apache.org/dist/pig/pig-${PIG_VERSION}/pig-${PIG_VERSION}.tar.gz | tar xz -C /opt \
 && mv /opt/pig-${PIG_VERSION} /opt/pig \
 && curl -fsSL https://archive.apache.org/dist/flume/${FLUME_VERSION}/apache-flume-${FLUME_VERSION}-bin.tar.gz | tar xz -C /opt \
 && mv /opt/apache-flume-${FLUME_VERSION}-bin /opt/flume \
 # guava 11 de Flume choca con la de Hadoop 3 (NoSuchMethodError en el sink HDFS)
 && rm -f /opt/flume/lib/guava-*.jar

FROM apache/hadoop:3.3.6
COPY --from=dl /opt/pig /opt/pig
COPY --from=dl /opt/flume /opt/flume
ENV PIG_HOME=/opt/pig \
    FLUME_HOME=/opt/flume \
    PATH=$PATH:/opt/pig/bin:/opt/flume/bin
CMD ["sleep", "infinity"]
