#!/bin/bash
python -m pyauto.core.tool -d examples/basic/ -o objects.yml -t tasks.yml -p packages.yml run ls-l2 cmd:shell.Command.run_command
