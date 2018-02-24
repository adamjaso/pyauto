import six
import shlex
import importlib


class Function(object):
    def __init__(self, func_str):
        value = shlex.split(func_str)
        self.func_str = func_str
        self.args = value[1:]
        parts = value[0].split('.')
        module_name = '.'.join(parts[0:-1])
        func_name = parts[-1]
        self.module = importlib.import_module(module_name)
        self.func = getattr(self.module, func_name)

    def run(self, **kwargs):
        value = self.func(*self.args, **kwargs)
        if isinstance(value, six.binary_type):
            value = value.decode('utf-8')
        return value
