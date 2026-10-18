FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml LICENSE ./
COPY src ./src
COPY contracts ./contracts
COPY core ./core
COPY adapters ./adapters
COPY services ./services
COPY sdk ./sdk
RUN pip install --no-cache-dir .
COPY config ./config
COPY examples ./examples
USER 65532:65532
CMD ["python", "examples/minimal.py"]
