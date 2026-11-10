FROM python:3.13-slim-bookworm@sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72 AS dependencies
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/backend PIP_DISABLE_PIP_VERSION_CHECK=1
RUN groupadd --gid 10001 inventario && useradd --uid 10001 --gid 10001 --create-home inventario
WORKDIR /app/backend
COPY backend/requirements.txt backend/requirements-deploy.txt ./
RUN python -m pip install --no-cache-dir -r requirements-deploy.txt && python -m pip check
FROM dependencies AS test-dependencies
COPY backend/requirements-test.txt ./
RUN python -m pip install --no-cache-dir -r requirements-test.txt && python -m pip check

FROM dependencies AS source
COPY --chown=10001:10001 backend/ ./
COPY --chown=10001:10001 deploy/ ./deploy/
COPY specs/003-fichas-adquisiciones/migration-notes/faculty_contract.py.txt /app/specs/003-fichas-adquisiciones/migration-notes/faculty_contract.py.txt
RUN mkdir -p /app/backend/staticfiles && chown 10001:10001 /app/backend/staticfiles
FROM source AS test
COPY --from=test-dependencies /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=test-dependencies /usr/local/bin /usr/local/bin
USER 10001:10001

FROM source AS runtime
USER 10001:10001
ENV DJANGO_SETTINGS_MODULE=config.settings_deploy
EXPOSE 8000
CMD ["python", "deploy/start.py"]
