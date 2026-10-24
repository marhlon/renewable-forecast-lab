FROM python:3.12.13-slim-bookworm
ENV DEBIAN_FRONTEND=noninteractive \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SPARK_LOCAL_IP=127.0.0.1 \
    PYSPARK_PYTHON=/usr/local/bin/python
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt
# UID/GID numéricos sozinhos não cadastram um usuário para Java/Hadoop.
# Esta camada vem depois das dependências para reaproveitar o build anterior.
RUN groupadd --gid 10001 renewcast \
    && useradd --uid 10001 --gid 10001 --no-create-home \
       --home-dir /tmp/renewcast --shell /usr/sbin/nologin renewcast
WORKDIR /tmp
USER renewcast:renewcast
ENTRYPOINT ["python", "/work/tools/m07_transformacao.py"]
