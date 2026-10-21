# Host

The service shell around the insight agent.

- `server.py` listens on port 8010 for the operator console.
- `product.py` and `product.html` are the question page on port 8030.
- `settings.py` holds the admin connection names.
- `observe.py` keeps the content-free event list.
- `tracking.py` records one MLflow run per question.
