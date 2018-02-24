.PHONY: py3 py2 deps3 deps2 deps3-dev deps2-dev test3 test2 test deps deploy

py3:
	[[ ! -d env3 ]] && virtualenv -p python3 env3 || :

py2:
	[[ ! -d env ]] && virtualenv env || :

deps3: py3
	. env3/bin/activate && pip install -r requirements.txt ; deactivate

deps2: py2
	. env/bin/activate && pip install -r requirements.txt ; deactivate

deps3-dev: deps3
	. env3/bin/activate && pip install -r requirements-dev.txt ; deactivate

deps2-dev: deps2
	. env/bin/activate && pip install -r requirements-dev.txt ; deactivate

test3: deps3-dev
	. env3/bin/activate && PYTHONPATH=../core:../util nose2 -v ; deactivate

test2: deps2-dev
	. env/bin/activate && PYTHONPATH=../core:../util nose2 -v ; deactivate

deps: deps3-dev deps2-dev

test: test3 test2

deploy: test
	python setup.py sdist upload -r https://upload.pypi.org/legacy/
