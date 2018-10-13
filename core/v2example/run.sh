#!/usr/bin/env bash
python -m pyauto.core.tool \
    -d v2example \
    -p requirements.yml \
    -t tasks.yml \
    -o repository.yml \
    run '{reg: {all: true}, app:{all: true}}' deploy_app
