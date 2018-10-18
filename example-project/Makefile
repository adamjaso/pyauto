PIP_INSTALL := pip install
PYTHON := python3
VENV := virtualenv -p $(PYTHON)
ENV := env
ACTIVATE := source $(ENV)/bin/activate
PYAUTO := $(ACTIVATE) && $(PYTHON) -m pyauto.core.tool

.PHONY: install
install:
	[[ ! -d "$(ENV)" ]] && $(VENV) $(ENV) ; \
	$(ACTIVATE) && $(PIP_INSTALL) -r requirements.txt

.PHONY: config
config:
	$(PYAUTO) \
		-p requirements.yml \
		-t tasks.yml \
		-o config.yml \
		run '{}' create_configs

.PHONY: all
all:
	$(PYAUTO) \
		-p requirements.yml \
		-t config/all-config-tasks.yml \
		-o config/all-configs.yml \
		run '{}' $(TASK)

.PHONY: all-inspect
all-inspect:
	$(PYAUTO) \
		-p requirements.yml \
		-t config/all-config-tasks.yml \
		-o config/all-configs.yml \
		run '{site: {all: true}}' site_all -i

