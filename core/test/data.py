from pyauto.core import api
from pyauto.util import yamlutil


example_task_sequences = """
arguments:
  region: {reg: deploy.Region}
  application: {reg: deploy.Region, app: deploy.App}
sequences:
  region_login:
    region:
      - task: deploy.Region.login {{reg.tag}}

  clone_app:
    application:
      - task: file.Directory.rmtree {{reg.tag}}_{{app.tag}}
      - task: file.Directory.copytree {{reg.tag}}_{{app.tag}}

  render_template:
    application:
      - task: file.File.render_template {{reg.tag}}_{{app.tag}}

  push_app:
    application:
      - task: deploy.RegionApp.push_app {{reg.tag}}_{{app.tag}}

  deploy_app:
    application:
      - seq: region_login
      - seq: clone_app
      - seq: render_template
      - seq: push_app
"""

sequences = yamlutil.load_dict(example_task_sequences)

example_query = """
{app: {tags: [a, b, c]}, reg: {labels: [abc]}}
"""

query = yamlutil.load_dict(example_query)

example_objects = """
---
kind: deploy.Region
tag: abc1
labels:
- abc
---
kind: deploy.Region
tag: abc2
labels:
- def
- abc
---
kind: deploy.Region
tag: abc3
labels:
- ghi
- abc
---
kind: deploy.App
tag: a
---
kind: deploy.App
tag: b
---
kind: deploy.App
tag: c

---
kind: file.File
tag: abc1_a
---
kind: file.File
tag: abc1_b
---
kind: file.File
tag: abc1_c
---
kind: file.File
tag: abc2_a
---
kind: file.File
tag: abc2_b
---
kind: file.File
tag: abc2_c
---
kind: file.File
tag: abc3_a
---
kind: file.File
tag: abc3_b
---
kind: file.File
tag: abc3_c

---
kind: file.Directory
tag: abc1_a
---
kind: file.Directory
tag: abc1_b
---
kind: file.Directory
tag: abc1_c
---
kind: file.Directory
tag: abc2_a
---
kind: file.Directory
tag: abc2_b
---
kind: file.Directory
tag: abc2_c
---
kind: file.Directory
tag: abc3_a
---
kind: file.Directory
tag: abc3_b
---
kind: file.Directory
tag: abc3_c

---
kind: deploy.RegionApp
tag: abc1_a
---
kind: deploy.RegionApp
tag: abc1_b
---
kind: deploy.RegionApp
tag: abc1_c
---
kind: deploy.RegionApp
tag: abc2_a
---
kind: deploy.RegionApp
tag: abc2_b
---
kind: deploy.RegionApp
tag: abc2_c
---
kind: deploy.RegionApp
tag: abc3_a
---
kind: deploy.RegionApp
tag: abc3_b
---
kind: deploy.RegionApp
tag: abc3_c
"""

objects = [o for o in yamlutil.load_dict(example_objects, load_all=True)]

example_packages = """
---
package: file
version: 0.0.0
kinds:
  - kind: Directory
    configs: test.data.Directory
    tasks:
      - rmtree
      - copytree
  - kind: File
    configs: test.data.File
    tasks:
      - render_template
---
package: deploy
version: 0.0.0
kinds:
  - kind: Region
    configs: test.data.Region
    tasks:
      - login
  - kind: App
    configs: test.data.Region
    tasks: []
  - kind: RegionApp
    configs: test.data.RegionApp
    tasks:
      - push_app
"""

packages = [p for p in yamlutil.load_dict(example_packages, load_all=True)]


class Directory(api.KindObject):
    def rmtree(self):
        pass

    def copytree(self):
        pass


class File(api.KindObject):
    def render_template(self):
        pass


class Region(api.KindObject):
    def login(self):
        pass


class App(api.KindObject):
    pass


class RegionApp(api.KindObject):
    def push_app(self):
        pass
