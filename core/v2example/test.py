import os
import json
from pyauto.util import yamlutil
from pyauto.core import api


dirname = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(dirname, 'pkg_.yml')) as f:
    packages = [pkg for pkg in yamlutil.load_dict(f, load_all=True)]


class Base(api.KindObject):
    def __init__(self, repo, obj):
        super(Base, self).__init__(repo, obj)
        self.obj = obj

    def __str__(self):
        return json.dumps(self.obj, indent=2)

    def __repr__(self):
        return self.__str__()


class T1(Base):
    def inspect(self, **kwargs):
        return self.obj


class T2(Base):
    def inspect(self, **kwargs):
        print(self.obj.e.value)


class T3(Base):
    pass


class T4(Base):
    pass
