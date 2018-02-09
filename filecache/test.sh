#!/bin/bash
source env3/bin/activate
PYTHONPATH=../local:../util:../core nose2 -v
deactivate
