
test:
	source venv/bin/activate && python -m pytest -x -vs -s --capture=no

publish:
	poetry config http-basic.pypi __token__ $(PYPI_TOKEN)
	poetry build
	poetry publish
