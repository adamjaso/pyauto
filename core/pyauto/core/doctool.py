from __future__ import print_function
import re
import os
import six
import sys
import pkgutil
import inspect
import importlib
from collections import OrderedDict
from copy import deepcopy
from . import config


def getdoc(obj):
    string = inspect.getdoc(obj)
    if string:
        return string.strip()
    else:
        return string


def log(*args):
    print(*args)


class Member(object):
    def __init__(self, module, member_name):
        self.module = module
        self.member = getattr(module, member_name)

    @property
    def name(self):
        return '.'.join([self.module.__name__, self.member.__name__])

    def is_command_func(self):
        if not inspect.isfunction(self.member):
            return False
        arg_names = inspect.getargspec(self.member)[0]
        if len(arg_names) < 1:
            return False
        return 'config' == arg_names[0]

    def is_config_class(self):
        if not inspect.isclass(self.member):
            return False
        if not issubclass(self.member, config.Config):
            return False
        if self.member == config.Config:
            return False
        return True

    def is_helper_function(self):
        return inspect.isfunction(self.member) and \
            self.member.__module__ == self.module.__name__

    def to_dict(self):
        if self.is_command_func():
            argspec = inspect.getargspec(self.member)
            argstr = inspect.formatargspec(*argspec)
            return OrderedDict([
                ('name', self.member.__name__),
                ('fullname', self.name),
                ('module', self.module.__name__),
                ('kind', 'command'),
                ('fullargstring', argstr),
                ('argstring', re.sub('^\(config, ', '(', argstr)),
                ('description', getdoc(self.member)),
            ])

        elif self.is_config_class():
            classmethods = self.get_class_methods()
            return OrderedDict([
                ('name', self.member.__name__),
                ('fullname', self.name),
                ('module', self.module.__name__),
                ('kind', 'config'),
                ('config_key', self.config_key),
                ('description', getdoc(self.member)),
                ('classmethods', self.get_class_methods()),
            ])

        elif self.is_helper_function():
            argspec = inspect.getargspec(self.member)
            return OrderedDict([
                ('name', self.member.__name__),
                ('fullname', self.name),
                ('module', self.module.__name__),
                ('kind', 'helperfunction'),
                ('argstring', inspect.formatargspec(*argspec)),
                ('description', getdoc(self.member))
            ])

        else:
            return None

    def get_class_docs(self):
        class_attrs = self.get_class_attributes()
        for name, prop in class_attrs.items():
            if inspect.isfunction(prop) and not name.startswith('_'):
                argspec = inspect.getargspec(prop)
                is_resource = len(argspec[0]) > 1 or \
                        argspec.varargs is not None
                argstr = inspect.formatargspec(*argspec)
                yield OrderedDict([
                    ('name', name),
                    ('class', self.name),
                    ('module', self.module.__name__),
                    ('kind', 'classmethod'),
                    ('resource', is_resource),
                    ('argstring', re.sub('^\(self(, )?', '(', argstr)),
                    ('description', getdoc(prop)),
                ])

    def get_class_methods(self):
        for name, cls in config.list_config_classes():
            if cls == self.member or (
                    inspect.ismethod(cls) and cls.__self__ == self.member):
                self.config_key = name
                break
        else:
            self.config_key = None
        return sorted(self.get_class_docs(),
                                  key=lambda doc: doc['name'])

    def get_class_attributes(self):
        cls = self.member
        boring = dir(type('dummy', (object,), {}))
        if hasattr(cls, '__dict__'):
            attrs = cls.__dict__.copy()
        elif hasattr(cls, '__slots__'):
            if hasattr(base, base.__slots__[0]): 
                # We're dealing with a non-string sequence or one char string
                for item in base.__slots__:
                    attrs[item] = getattr(base, item)
                else: 
                    # We're dealing with a single identifier as a string
                    attrs[base.__slots__] = getattr(base, base.__slots__)
        for key in boring:
            if key in attrs:
                del attrs[key]  # we can be sure it will be present so no need to guard this
        return attrs


class Module(object):
    def __init__(self, module_name, parent=None):
        self.module = importlib.import_module(module_name)

    def list_modules(self):
        for importer, modname, ispkg in pkgutil.iter_modules(
                self.module.__path__):
            yield importlib.import_module('.' + modname, self.module.__name__)

    def get_commands(self, module):
        commands = []
        for member in inspect.getmembers(module):
            if member[0].startswith('_'):
                continue
            mem = Member(module, member[0])
            res = mem.to_dict()
            if res is not None:
                commands.append(res)
        commands = sorted(commands, key=lambda c: c['fullname'])
        return OrderedDict([
            ('name', module.__name__),
            ('module', self.module.__name__),
            ('description', getdoc(module)),
            ('members', commands),
        ])

    def extract_commands(self):
        res = OrderedDict()
        if hasattr(self.module, '__path__'):
            for mod in self.list_modules():
                if mod.__name__ in res:
                    log(mod.__name__, 'was already detected!')
                res[mod.__name__] = self.get_commands(mod)
        else:
            res[self.module.__name__] = self.get_commands(self.module)
        return res


def aggregate_results(data):
    kinds = OrderedDict()
    modules = OrderedDict()
    for module_name, module_spec in data.items():
        mspec = deepcopy(module_spec)
        del mspec['members']
        modules[module_name] = mspec
        for member in module_spec['members']:
            if member['kind'] not in kinds:
                kinds[member['kind']] = []
            if member['kind'] == 'config':
                member['resources'] = [
                    deepcopy(m) for m in member['classmethods']
                    if m['resource']]
            kinds[member['kind']].append(member)
    for kind, members in kinds.items():
        kinds[kind] = sorted(kinds[kind], key=lambda k: k['fullname'])
    return OrderedDict([
        ('kinds', kinds),
        ('modules', modules)
    ])


def aggregate_per_module(data):
    results = OrderedDict()
    for module_name, module_spec in data.items():
        results[module_name] = aggregate_results({module_name: module_spec})
    return results


def merge_config_docs(docs, results):
    for module_name, spec in  results.items():
        if 'config' in spec['kinds']:
            for member in spec['kinds']['config']:
                properties = docs['config'].get(member['fullname'], [])
                if isinstance(properties, (dict, OrderedDict)):
                    properties = [
                        OrderedDict([
                            ('name', name),
                            ('description', value)])
                        for name, value in properties.items()]
                member['properties'] = properties


def main():
    import sys
    import json
    import argparse
    from pyauto.util import yamlutil
    from pyauto.core import template

    args = argparse.ArgumentParser()
    args.add_argument('-t', '--template', dest='template', default=None)
    args.add_argument('-o', '--output', dest='output', default='-')
    args.add_argument('--merge-docs', dest='merge_docs', default=None)
    args.add_argument('--aggregate', dest='aggregate', action='store_true')
    args.add_argument('--format', dest='format',
                      choices=['yaml', 'json'], default='yaml')
    args.add_argument('modules', nargs='+')
    args = args.parse_args()

    data = OrderedDict()
    for module_name in args.modules:
        pkg = Module(module_name)
        data.update(pkg.extract_commands())

    if args.aggregate:
        data = aggregate_per_module(data)

        if args.merge_docs:
            docs_path = os.path.abspath(args.merge_docs)
            with open(docs_path) as f:
                docs = yamlutil.load_dict(f)
            merge_config_docs(docs, data)


    if args.template:
        data = template.render_file(args.template, data=data)
    elif 'json' == args.format:
        data = json.dumps(data, indent=2)
    else:
        data = yamlutil.dump_dict(data)

    if '-' == args.output:
        sys.stdout.write(data)
    else:
        output = os.path.abspath(args.output)
        with open(output, 'w') as f:
            f.write(data)


if '__main__' == __name__:
    main()
