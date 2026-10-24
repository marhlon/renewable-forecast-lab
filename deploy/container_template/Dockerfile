ARG PYTHON_BASE
FROM ${PYTHON_BASE} AS dependencies
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /capture
COPY requirements.versions.txt ./
# As versões são preservadas; os binários precisam corresponder ao Linux.
RUN python -m pip download --only-binary=:all: --no-deps --dest /wheels -r requirements.versions.txt
COPY service.whl /service.whl
COPY lock_linux.py ./
RUN python lock_linux.py

FROM ${PYTHON_BASE} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY --from=dependencies /wheels /wheels
COPY --from=dependencies /requirements.linux.lock /requirements.linux.lock
RUN python -m pip install --no-index --only-binary=:all: --find-links /wheels --require-hashes -r /requirements.linux.lock && python -m pip check
WORKDIR /app
COPY artifacts /app/artifacts
COPY reference_response.json context.json serve.py /app/
RUN python -c "import json,platform; x=json.load(open('context.json')); assert platform.python_version()==x['python_version'], 'Python da imagem diverge do protocolo'"
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=20s --retries=6 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=2)"]
CMD ["python", "/app/serve.py"]
