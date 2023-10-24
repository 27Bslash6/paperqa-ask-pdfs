SHELL := /bin/bash

ENV ?= dev
USERNAME ?= $(shell whoami)

VIRTUALENV_NAME ?= asq

.PHONY: init-requirements init-vector-store binary

init: init-requirements init-vector-store

.python-version:
	pyenv virtualenv 3.11 $(VIRTUALENV_NAME)
	pyenv local $(VIRTUALENV_NAME)

init-requirements: .python-version
	pip install -r requirements.txt

init-vector-store:
	wrangler vectorize create asq-$(USERNAME)-$(ENV) --metric=METRICS --dimensions=DIMENSIONS

binary:
	pyinstaller --onefile aks.py

aks: check-OPENAI_API_KEY
	python aks.py -i

.PHONY: check-% ## Check variable exists. Use by adding a dependency named `check-<VARIABLE_NAME>`.
check-%:
	@: $(if $(value $*),,$(error $* is undefined))
