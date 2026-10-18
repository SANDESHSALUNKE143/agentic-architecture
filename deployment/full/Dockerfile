FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml LICENSE ./
COPY src ./src
COPY contracts ./contracts
COPY core ./core
COPY adapters ./adapters
COPY services ./services
COPY sdk ./sdk
RUN pip install --no-cache-dir '.[service,providers,telemetry,platform]'
USER 65532:65532
CMD ["python","-m","uvicorn","agentic_sdk.hosted:create_app","--factory","--host","0.0.0.0","--port","8020"]
