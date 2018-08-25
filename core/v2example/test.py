import json


class Base(object):
    def __init__(self, obj):
        self.obj = obj

    def __str__(self):
        return json.dumps(self.obj.data, indent=2)

    def __repr__(self):
        return self.__str__()


class T1(Base):
    def inspect(self, **kwargs):
        print(self)


class T2(Base):
    def inspect(self, **kwargs):
        print(self.obj.e.value)


class T3(Base):
    pass


class T4(Base):
    pass
