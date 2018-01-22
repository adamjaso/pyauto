#!/bin/bash
PYTHONPATH=../util nose2 -v
. env3/bin/activate
cd examples/simple
python -m pyauto.core.deploy -c config.yml
python -m pyauto.core.deploy -c config.yml deploy_my_app -i
python -m pyauto.core.deploy -c config.yml deploy_my_app -t
python -m pyauto.core.deploy -c config.yml deploy_app,my_app
