# pyauto

A task running tool

## What is this?

PyAuto provides a minimalist project structure for capturing configuration and orchestrating tasks.

### What is a Task?

A python function.

```python
# deployment_tasks.py

# this needs to be imported so that the config class will be registered
import deployment_config


def deploy_app(config, app_name):
    # implement deployment here
    print('deploying {0}...'.format(app_name))
    app = config.apps.get_tag(app_name)
    print(app)
```

### How is it configured?

YAML + Python Class.

```
# config.yml
task_modules:
- deployment_tasks
apps:
- id: my_app
  name: My Application
  source_dir: ./my_app
tasks:
  deploy_my_app:
  - deploy_app,my_app
```

```python
# deployment_config.py

from pyauto import config
import os


class App(config.Config):
    def get_source_dir(self):
        return os.path.abspath(self.source_dir)


config.set_config_class('apps', App.wrap)
```

### How is it used?

As a CLI tool.

#### Run the task

```bash
$ python -m pyauto.deploy -c config.yml deploy,my_app
```

Outputs

```
----- deployment_tasks.deploy_app ( my_app  ) -----
deploying my_app...
OrderedDict([('id', 'my_app'), ('name', 'My Application'), ('source_dir', './my_app')])
deploy_app,my_app = None
```

The "," separates the function from the string arguments. All task functions
*must* accept string only arguments.

#### Run a sequence of tasks

```bash
$ python -m pyauto.deploy -c config.yml deploy_my_app
```

Outputs

```
----- deployment_tasks.deploy_app ( my_app  ) -----
deploying my_app...
OrderedDict([('id', 'my_app'), ('name', 'My Application'), ('source_dir', './my_app')])
deploy_app,my_app = None
```

Line 1 of the output indicates the function invoked, with the arguments passed to it.
Lines 2-3 of the output indicate the standard output of the function's execution
Last line of the output indicates 1) the original function invocation string and 2) the return value of the function.

If you wish to suppress output of line 1 and last line, you can pass the `-q` option to have PyAuto omit those lines.

The task sequence `deploy_my_app` is looked up from the `tasks` section of the config.
A task sequence may list as many tasks or task sequences as desired. Every item
will always be executed when the task sequence is invoked.

#### Dry-run a sequence of tasks

```bash
$ python -m pyauto.deploy -c config.yml deploy_my_app -i
```

Outputs

```
deploy_my_app (  )
    deployment_tasks.deploy_app ( my_app )
```

This shows the sequence of tasks that will be run. This is a trivial example,
but you may also invoke other task sequences from a task sequence, which can
lead to a complex order of tasks. This feature allows you to inspect what a given
task sequence will execute before you execute it.
