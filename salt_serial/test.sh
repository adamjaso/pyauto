#!/bin/bash
if [ -d env ] ; then
    source env/bin/activate
    python --version
    PYTHONPATH=../core:../local:../util nose2 -v
    deactivate
fi

if [ -d env3 ] ; then
    source env3/bin/activate
    python --version
    PYTHONPATH=../core:../local:../util nose2 -v
    deactivate
fi
