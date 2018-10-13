import os
import json
from pyauto.core import api
from pyauto.util import yamlutil


packages = api.read_packages(__file__, 'package.yml')


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
