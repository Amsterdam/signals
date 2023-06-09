# This Makefile is based on the Makefile defined in the Python Best Practices repository:
# https://git.datapunt.amsterdam.nl/Datapunt/python-best-practices/blob/master/dependency_management/
#
# VERSION = 2020.01.29

PYTHON = python3

help:                               ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

pip-tools:
	pip install pip-tools

install: pip-tools                  ## Install requirements and sync venv with expected state as defined in requirements.txt
	pip-sync requirements/requirements.txt requirements/requirements_dev.txt

requirements: pip-tools             ## Upgrade requirements (in requirements.in) to latest versions and compile requirements.txt
	pip-compile --upgrade --output-file requirements/requirements.txt requirements/requirements.in
	pip-compile --upgrade --output-file requirements/requirements_test.txt requirements/requirements_test.in
	pip-compile --upgrade --output-file requirements/requirements_dev.txt requirements/requirements_dev.in

upgrade: requirements install       ## Run 'requirements' and 'install' targets
