.PHONY: py3 py2 install3 install2 install3-dev install2-dev test3 test2 test install deploy docs

py3:
	[[ ! -d env3 ]] && virtualenv -p python3 env3 || :

py2:
	[[ ! -d env ]] && virtualenv env || :

install3: py3
	. env3/bin/activate && pip install -r requirements.txt ; deactivate

install2: py2
	. env/bin/activate && pip install -r requirements.txt ; deactivate

install3-dev: install3
	. env3/bin/activate && pip install -r requirements-dev.txt ; deactivate

install2-dev: install2
	. env/bin/activate && pip install -r requirements-dev.txt ; deactivate

test3: install3-dev
	. env3/bin/activate && nose2 -v

test2: install2-dev
	. env/bin/activate && nose2 -v

install: install3-dev install2-dev

test: test3 test2

deploy: test docs
	python setup.py sdist upload -r https://upload.pypi.org/legacy/

docs:
	pandoc --from=markdown --to=rst --output=README.rst README.md
