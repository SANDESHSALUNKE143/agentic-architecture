# Compatibility test guide

Relevant checks: test_layout.py validates that old and architectural imports reference identical classes; test_core.py retains the RAG compatibility baseline.

Executable unit modules remain in the parent tests folder for unittest discovery. This folder documents coverage and does not contain a second implementation of those tests.
