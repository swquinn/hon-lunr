.PHONY: clean-pyc
clean-pyc:
	@echo "> Cleaning .pyc files..."
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +

.PHONY:install.dev
install.dev:
	pip3 install -e ".[dev]"

.PHONY: test
test: clean-pyc
	tox

.PHONY:uninstall.dev
uninstall.dev:
	pip3 uninstall hon-lunr