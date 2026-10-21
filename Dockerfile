FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .
COPY deployment/config ./deployment/config
COPY examples ./examples
USER 65532:65532
CMD ["python", "examples/minimal.py"]
