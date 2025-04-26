coverage-html:
	pytest --cov=src --cov-report=html
	open htmlcov/index.html 