FROM python:3.12-slim
WORKDIR /opt/sdk
COPY --from=sdk pyproject.toml LICENSE ./
COPY --from=sdk src ./src
RUN pip install --no-cache-dir '.[service,platform]' \
 && python -c "from pathlib import Path; import agentic_sdk.services.operator_ui as ui; Path(ui.__file__).with_name('page.html').write_bytes(Path('/opt/sdk/src/services/operator_ui/page.html').read_bytes())"
EXPOSE 8020
CMD ["python", "-m", "uvicorn", "agentic_sdk.services.operator_ui.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8020"]
