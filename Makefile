.PHONY: docs

docs:
	rm -rf docs/_build/html
	find docs/api ! -name 'index.rst' -type f -exec rm -f {} +
	pip install -qr docs/requirements.txt
	pip install -r requirements.txt
	pip install -r requirements_dev.txt
	pip install -e .
	jb build docs