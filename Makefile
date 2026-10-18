.PHONY: test example eval validate build
test:
	python -m unittest discover -s tests -v
example:
	python examples/minimal.py
eval:
	python evaluation/run.py
validate:
	python scripts/validate_config.py
	docker compose config --quiet
build:
	python -m build
