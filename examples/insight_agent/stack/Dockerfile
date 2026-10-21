FROM python:3.12-slim
WORKDIR /opt/sdk
COPY --from=sdk pyproject.toml LICENSE ./
COPY --from=sdk src ./src
RUN pip install --no-cache-dir '.[service,providers,platform,telemetry]' \
    && pip install --no-cache-dir 'neo4j>=5.26,<6'
WORKDIR /app
COPY pyproject.toml ./
COPY *.py ./
COPY perception ./perception
COPY cognition ./cognition
COPY action ./action
COPY environment ./environment
COPY learning ./learning
COPY communication ./communication
COPY host ./host
RUN pip install --no-cache-dir --no-deps .
ENV PYTHONUNBUFFERED=1
EXPOSE 8010 8030
CMD ["python", "-m", "insight_agent"]
