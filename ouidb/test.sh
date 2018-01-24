#!/bin/bash
source env3/bin/activate
PYTHONPATH=../local:../util nose2 -v
deactivate
