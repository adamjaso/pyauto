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
