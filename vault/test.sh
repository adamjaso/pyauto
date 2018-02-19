#!/bin/bash
source env3/bin/activate
PYTHONPATH=../core:../local:../util nose2 -v
deactivate
