.PHONY: clean-pyc clean-build help

export PYTHONPATH=.:./scheduler

clean: clean-build clean-pyc

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

black:
	echo "========== Running Black  ==========="
	poetry run black scheduler bdd -l 79

flake8:
	echo "========== Running flake8 ==========="
	poetry run flake8

bandit:
	echo "========== Running bandit ==========="
	poetry run bandit -r . -ll

isort:
	echo "========== Isort ===================="
	poetry run isort scheduler bdd

lint: isort black flake8 bandit

test:
	poetry run pytest bdd/tests

coverage:
	poetry run pytest --cov ./scheduler --cov-report html:cov_html --cov-report term-missing bdd/tests

pre-pipeline-check: lint coverage

migrate:
	python scheduler\manage.py migrate

# =========================================
# ====== Deployment (out of poetry) =======
# =========================================

unittest:
	poetry run pytest --junitxml=test-results/pytest.xml --cov ./scheduler --cov-report=xml --cov-report term-missing bdd/tests
