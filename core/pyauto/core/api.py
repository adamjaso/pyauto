import os
import re
import sys
import six
import time
import json
import shlex
import jinja2
import logging
import itertools
import importlib
from logging import StreamHandler
from copy import deepcopy
from pyauto.util import yamlutil
from collections import OrderedDict


logger = logging.getLogger('pyauto.core')


def setup_logger(logger):
    formatter = logging.Formatter('%(message)s')
    handler = StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def read_packages(filename, neighbor=None):

    def _read_packages(filename):
        if os.path.isfile(filename):
            with open(filename) as f:
                for item in yamlutil.load_dict(f, load_all=True):
                    if isinstance(item, list):
                        for obj in item:
                            yield obj
                    else:
                        yield item
        elif os.path.isdir(filename):
            for dirpath, dirnames, filenames in os.walk(filename):
                for filename in filenames:
                    filename = os.path.join(dirpath, filename)
                    with open(filename) as f:
                        for item in yamlutil.load_dict(f, load_all=True):
                            if isinstance(item, list):
                                for obj in item:
                                    yield obj
                            else:
                                yield item
        else:
            raise PyautoException('Not a file or directory: {0}'
                                  .format(filename))

    if neighbor is not None:
        filename = os.path.join(
            os.path.dirname(os.path.abspath(filename)), neighbor)

    return list(_read_packages(filename))


def get_output_object(
        task=None, obj=None, time=None, duration=None, result=None):
    if not isinstance(result, (dict, OrderedDict, list, int, float)) and \
            not isinstance(result, six.string_types):
        result = str(result)
    return OrderedDict([
        ('task', task.name),
        ('obj', obj.ref),
        ('time', time),
        ('duration', duration),
        ('result', result),
    ])


class Repository(object):
    def __init__(self):
        self._data = OrderedDict()
        self._packages = OrderedDict()

    @property
    def data(self):
        return self._data

    @property
    def kinds(self):
        return [k.kind for k in self._data.values()]

    def query(self, q, **options):
        result = OrderedDict()
        for kindstr, objs in q.items():
            result[kindstr] = self.get(kindstr).query(objs, **options)
            if options.get('resolve', False):
                result[kindstr] = [i for i in result[kindstr]]
        return result

    def invoke(self, taskref, tag, args):
        args = args or {}
        ref = TaskReference(taskref)
        obj = self[ref.kind][tag]
        kt = self[ref.kind].kind.tasks[ref.name]
        start = time.time()
        res = kt.invoke(obj, **args)
        duration = time.time() - start
        return get_output_object(
            task=kt,
            obj=obj,
            time=start,
            duration=duration,
            result=res,
        )

    def invoke_kind_task(self, kind, tag, task, args):
        args = args or {}
        obj = self[kind][tag]
        kt = self[kind].kind.tasks[task]
        start = time.time()
        res = kt.invoke(obj, **args)
        duration = time.time() - start
        return get_output_object(
            task=kt,
            obj=obj,
            time=start,
            duration=duration,
            result=res,
        )

    def dump(self):
        for obj in self:
            yield obj.dump()

    def dump_packages(self):
        for pkg in self._packages.values():
            yield pkg.data

    def __repr__(self):
        return json.dumps({
            self.__class__.__name__: OrderedDict([
                (kind, len(objs))
                for kind, objs in self._data.items()
            ])
        })

    def __iter__(self):
        for kind, objs in self._data.items():
            for obj in objs:
                yield obj

    def __len__(self):
        total = 0
        for _, objs in self._data.items():
            total += len(objs)
        return total

    def assert_package(self, package):
        if package not in self._packages:
            raise UnknownPackageException(package)

    def assert_kind(self, kind):
        if str(kind) not in self._data:
            raise UnknownKindException(kind)

    def assert_object(self, kind, tag):
        self.assert_kind(kind)
        self._data[kind].assert_object(tag)

    def get(self, ref):
        if not isinstance(ref, Reference):
            ref = Reference(ref)
        if ref.tag:
            self.assert_object(ref.kind, ref.tag)
            return self._data[ref.kind][ref.tag]
        else:
            self.assert_kind(ref.kind)
            return self._data[ref.kind]

    def __getitem__(self, item):
        return self.get(item)

    def __contains__(self, ref):
        if not isinstance(ref, Reference):
            ref = Reference(ref)
        if ref.tag:
            self.assert_kind(ref.kind)
            return ref.tag in self._data[ref.kind]
        else:
            return ref.kind in self._data

    def _add_kind(self, kind):
        if kind.name not in self._data:
            self._data[kind.name] = KindObjects(self, kind)
        else:
            self.assert_kind(kind.name)
        return self

    def add_package(self, package):
        if not isinstance(package, Package):
            package = deepcopy(package)
            package = Package(self, package)
        if package.name not in self._packages:
            self._packages[package.name] = package
            for kind in package.kinds:
                self._add_kind(kind)

    def get_package(self, package):
        self.assert_package(package)
        return self._packages[package]

    def get_kind(self, kind):
        self.assert_kind(kind)
        return self._data[str(kind)].kind

    def add(self, obj):
        if not isinstance(obj, (dict, OrderedDict)) or 'kind' not in obj:
            raise InvalidKindObjectException('Invalid kind object: {0}'
                                             .format(obj))
        kind_name = obj['kind']
        self.assert_kind(kind_name)
        return self._data[kind_name].add(obj)

    def load_packages_file(self, filename, neighbor=None):
        pkgs = read_packages(filename, neighbor)
        return self.load_packages(pkgs)

    def load_file(self, filename, neighbor=None):
        objs = read_packages(filename, neighbor)
        return self.load_objects(objs)

    def remove_package(self, pkg):
        self.assert_package(pkg.name)
        pkg = self._packages[pkg.name]
        for kind in pkg.kinds:
            for obj in self[kind.name]:
                self.remove(obj)
        del self._packages[pkg.name]

    def remove(self, obj):
        self.assert_kind(obj.kind.name)
        self._data[obj.kind.name].remove(obj)

    def load_packages(self, data):
        for package in data:
            self.add_package(package)
        self.validate_packages()
        return self

    def validate_packages(self):
        for kindobjs in self._data.values():
            kindobjs.kind.validate_relations(self)
        for name, package in self._packages.items():
            for dep in package.dependencies:
                self.assert_package(dep)

    def parse_objects(self, data):
        data = yamlutil.load_dict(data, load_all=True)
        return self.load_objects(data)

    def load_objects(self, data):
        for obj in data:
            self.add(deepcopy(obj))
        return self


class Reference(object):
    kind = None
    tag = None

    def __init__(self, tag):
        if not isinstance(tag, six.string_types):
            raise InvalidKindObjectReferenceException(tag)
        parts = tag.split('/')
        if len(parts) >= 1:
            self.kind = parts[0]
        if len(parts) >= 2:
            self.tag = parts[1]


class TaskReference(object):
    kind = None
    name = None

    def __init__(self, ref):
        if not isinstance(ref, six.string_types):
            raise InvalidKindTaskReferenceException(ref)
        parts = ref.split('.')
        if len(parts) != 3:
            raise InvalidKindTaskReferenceException(ref)
        self.kind = '.'.join(parts[:2])
        self.name = parts[2]


class KindAttributeDetail(object):
    kind = None
    name = None
    required = True
    list = False

    def __init__(self, package, name, spec):
        if not isinstance(spec, six.string_types):
            raise InvalidKindAttributeDetailException(spec)
        self.name = name
        parts = re.split('\s+', spec)
        for i, part in enumerate(parts):
            if 0 == i:
                self.kind = package.get_kind_name(part)
            elif 'optional' == part:
                self.required = False
            elif 'list' == part:
                self.list = True

    def __str__(self):
        return self.kind

    def __repr__(self):
        return self.__str__()

    def get_attribute(self, obj, repo):
        if self.name not in obj:
            if self.required:
                raise KindObjectAttributeException(
                    'Required attribute not found: {0}.{1}'
                    .format(self.kind, self.name))
            elif self.list:
                return []
            else:
                return None
        value = obj[self.name]
        if self.list:
            if not isinstance(value, list):
                raise KindObjectAttributeException(
                    'Invalid attribute type: {0}'.format(type(value)))
            return RelationList(obj, self.name, [
                repo[self.kind][tag] for tag in value])
        else:
            if isinstance(value, list):
                raise KindObjectAttributeException(
                    'Invalid attribute type: {0}'.format(type(value)))
            return Relation(obj, self.name, repo[self.kind][value])


class AttributeDetail(object):
    parsers = {
        'int': lambda n: int(str(n)),
        'hexint': lambda n: int(str(n), 16),
        'octint': lambda n: int(str(n), 8),
        'float': lambda n: float(str(n)),
        'string': six.text_type,
        'path': os.path.abspath,
        'envvar': os.getenv,
        'list': list,
        'map': OrderedDict
    }
    _parse = None
    kind = None
    name = None
    required = True

    def __init__(self, kind, name, key):
        self._parse = []
        self.kind = kind
        self.name = name
        parts = re.split('\s+', key)
        for i, part in enumerate(parts):
            if 0 == i:
                self._parse.append(self.resolve_parser(part))
            elif 'optional' == part:
                self.required = False
            else:
                self._parse.append(self.resolve_parser(part))

    def resolve_parser(self, typ):
        while isinstance(typ, six.string_types):
            if typ not in self.parsers:
                raise KindObjectAttributeException(
                    'Invalid attribute type: {0}'.format(typ))
            typ = self.parsers[typ]
        return typ

    def parse(self, value):
        for parser in self._parse:
            value = parser(value)
        return value

    def get_attribute(self, obj):
        if self.name not in obj:
            if self.required:
                raise KindObjectAttributeException(
                    'Required attribute not found: {0}.{1}'
                    .format(self.kind.name, self.name))
            else:
                return None
        value = obj[self.name]
        return self.parse(value)


class Package(object):
    def __init__(self, repo, package):
        self._repo = repo
        self._data = package
        self._dependencies = package.get('dependencies', [])
        self._kinds = [
            Kind(self, kind)
            for kind in package.get('kinds', [])
        ]

    @property
    def name(self):
        return self.get('package')

    @property
    def kinds(self):
        return self._kinds

    @property
    def repo(self):
        return self._repo

    @property
    def dependencies(self):
        return self._dependencies

    @property
    def data(self):
        return self._data

    def get_kind_name(self, name):
        if '.' in name:
            return name
        return '.'.join([self.name, name])

    def get_kind(self, name):
        for kind in self._kinds:
            if kind.package.name == self.name:
                return kind
        raise UnknownKindException(name)

    def get(self, item):
        return self._data.get(item, None)

    def __getitem__(self, item):
        return self.get(item)

    def __getattr__(self, name):
        return self.get(name)


class Kind(object):
    def __init__(self, package, kind):
        self._package = package
        self._data = kind
        self._kind = kind['kind']
        self.config_class = self._get_config_class()
        self.command_class = self._get_command_class()
        self._attributes = OrderedDict([
            (name, AttributeDetail(self, name, a))
            for name, a in kind.get('attributes', {}).items()
        ])
        self._relations = OrderedDict([
            (name, KindAttributeDetail(package, name, k))
            for name, k in kind.get('relations', {}).items()
        ])
        for name in self._relations:
            if name in self._attributes:
                raise InvalidKindException(
                    'Kind relations may not have the sam e as attributes: {0}'
                    .format(name))
        self._tasks = KindTasks(self, kind.get('tasks', []))

    def dump(self, obj):
        res = OrderedDict([
            ('kind', obj.kind.name),
            ('tag', obj.tag),
            ('labels', obj.labels)
        ])
        for name in self.attributes:
            res[name] = obj.data.get(name)
        for name in self.relations:
            res[name] = obj.data.get(name)
        return res

    @property
    def name(self):
        return '.'.join([self._package.name, self._kind])

    @property
    def package(self):
        return self._package

    @property
    def tasks(self):
        return self._tasks

    @property
    def relations(self):
        return self._relations

    @property
    def attributes(self):
        return self._attributes

    def __repr__(self):
        return json.dumps(self._data)

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __getitem__(self, item):
        return self._data.get(item, None)

    def __contains__(self, item):
        return item in self._data

    def validate_relations(self, repo):
        for name, kind in self._relations.items():
            repo.get_kind(kind)
        return self

    def _resolve_attribute(self, name, obj):
        if name not in self._attributes:
            raise KindObjectAttributeException(
                'Unknown attribute: {0} for {1}'.format(name, obj))
        return self._attributes[name].get_attribute(obj)

    def _resolve_relation(self, name, obj, repo):
        if name not in self.relations:
            raise KindObjectRelationException(
                'Unknown attribute relation: {0} for {1}'.format(name, obj))
        return self._relations[name].get_attribute(obj, repo)

    def resolve_attr(self, name, obj, repo):
        if name in self._attributes:
            return self._resolve_attribute(name, obj)
        elif name in self._relations:
            return self._resolve_relation(name, obj, repo)
        else:
            return obj.get(name)

    def _get_config_class(self):
        if 'configs' not in self:
            raise InvalidKindException(
                'Kind does not provide "configs": {0}'.format(self.name))
        parts = self['configs'].split('.')
        module_name, func_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_name)
        if not hasattr(module, func_name):
            raise InvalidKindException(
                'Kind "config" with name "{0}" was not found'
                .format(self['configs']))
        return getattr(module, func_name)

    def _get_command_class(self):
        if 'commands' not in self:
            return self._get_config_class()
        parts = self['commands'].split('.')
        module_name, func_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_name)
        if not hasattr(module, func_name):
            raise InvalidKindException(
                'Kind "commands" with name "{0}" was not found'
                .format(self['config']))
        return getattr(module, func_name)

    def get_module(self):
        return self._get_config_class()


class KindTasks(object):
    def __init__(self, kind, tasks):
        tasks = tasks or []
        self._kind = kind
        self._command_class = self._kind.command_class
        self._tasks = OrderedDict()
        for task in tasks:
            if isinstance(task, six.string_types):
                if not hasattr(self._command_class, task):
                    raise UnknownKindObjectTaskException(
                        'Module task not found: {0} for class {1}'.format(
                            task, self._command_class))
                self._tasks[task] = KindTask(self, self._command_class, task)
            else:
                raise InvalidKindObjectTaskException(
                    'Invalid task spec: {0}'.format(task))

    @property
    def kind(self):
        return self._kind

    def __contains__(self, item):
        self.assert_task(item)
        return item in self._tasks

    def __getitem__(self, item):
        self.assert_task(item)
        return self._tasks[item]

    def assert_task(self, task):
        if task not in self._tasks:
            raise UnknownKindObjectTaskException(
                'Task not found: {0}'.format(task))

    def parse_args(self, args):
        if isinstance(args, (dict, OrderedDict)):
            keys = [k for k in args.keys()]
            if len(keys) != 1:
                raise InvalidKindObjectTaskInvocationException(
                    'Invalid task invocation: {0}'.format(args))
            func_name = keys[0]
            kwargs = args[func_name]
        else:
            func_name = args
            kwargs = {}
        self.assert_task(func_name)
        return func_name, kwargs

    def invoke(self, obj, args):
        func_name, kwargs = self.parse_args(args)
        self.assert_task(func_name)
        return self._tasks[func_name].invoke(obj, **kwargs)


class KindTask(object):
    def __init__(self, tasks, module, task):
        self._tasks = tasks
        self._module = module
        self._task = task

    @property
    def name(self):
        return ''.join([self._tasks.kind.name, '.', self._task])

    @property
    def module_name(self):
        return ''.join([self._module.__name__, '.', self._task])

    @property
    def tasks(self):
        return self._tasks

    def invoke(self, obj, **args):
        if type(obj) == self._module:
            return getattr(obj, self._task)(**args)
        else:
            return getattr(self._module, self._task)(obj, **args)

    def __call__(self, obj, **args):
        return self.invoke(obj, **args)

    def __repr__(self):
        return ''.join(['<', self.__class__.__name__, ' ',
                        self._tasks.kind.name,
                        '.', self._task, '>'])


class KindObjects(object):
    def __init__(self, repo, kind):
        self._repo = repo
        self._kind = kind
        self._items = OrderedDict()
        self._labels = OrderedDict()

    @property
    def data(self):
        return self._items

    def query(self, data, **options):
        if data.get('all'):
            for obj in self._items.values():
                yield self.get_object(obj, **options)
            return

        tags = data.get('tags', [])
        if isinstance(tags, six.text_type):
            tags = [tags]
        elif not isinstance(tags, list):
            raise InvalidQueryException('Query tags must be a list')

        labels = data.get('labels', [])
        if isinstance(labels, six.text_type):
            labels = [labels]
        elif not isinstance(labels, list):
            raise InvalidQueryException('Query labels must be a list')

        seen = set()
        for result in self.query_tags(tags, **options):
            if result not in seen:
                seen.add(result)
                yield result
        for result in self.query_labels(labels, **options):
            if result not in seen:
                seen.add(result)
                yield result

    def query_tags(self, tags, **options):
        for obj in self._items.values():
            if obj.tag in tags:
                yield self.get_object(obj, **options)

    def query_labels(self, labels, **options):
        if len(labels) != len(set(labels)):
            raise InvalidQueryException('query_label requires a unique list')
        seen = set()
        for label in labels:
            for tag in self._labels.get(label, []):
                if tag not in seen:
                    seen.add(tag)
                    yield self.get_object(self[tag], **options)

    def get_object(self, obj, **options):
        if options.get('ref'):
            return obj.ref
        elif options.get('tag'):
            return obj.tag
        else:
            return obj

    @property
    def kind(self):
        return self._kind

    def assert_object(self, tag):
        if tag not in self._items:
            raise UnknownKindObjectException(self.kind.name, tag)

    def add(self, obj):
        if not isinstance(obj, KindObject):
            obj = self.kind.config_class(self._repo, obj)
        if obj.tag in self._items:
            raise DuplicateKindObjectException(kind_tag=obj.ref)
        self._items[obj.tag] = obj
        for label in obj.labels:
            self._add_label(label, obj.tag)
        return obj

    def _add_label(self, label, tag):
        if label not in self._labels:
            self._labels[label] = list()
        self._labels[label].append(tag)

    def _remove_label(self, label, tag):
        if label in self._labels:
            self._labels[label].remove(tag)
            return True
        return False

    def remove(self, obj):
        if obj.tag in self._items:
            for label in obj.labels:
                self._remove_label(label, obj.tag)
            del self._items[obj.tag]
            return True
        return False

    def __getitem__(self, item):
        self.assert_object(item)
        return self._items[item]

    def __contains__(self, item):
        return item in self._items

    def __iter__(self):
        return iter(self._items.values())

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        return ''.join(['<', self.__class__.__name__, ' ', self.kind.name, ' ',
                        json.dumps(self._items), '>'])


class KindObject(object):
    def __init__(self, repo, obj):
        self._repo = repo
        self._kind = repo.get_kind(obj['kind'])
        self._data = obj

    @property
    def ref(self):
        return '/'.join([self.kind.name, self.tag])

    @property
    def tag(self):
        return self['tag']

    @property
    def kind(self):
        return self._kind

    @property
    def data(self):
        return self._data

    @property
    def labels(self):
        return self.get('labels') or []

    def set_repo(self, repo):
        self._repo = repo
        return self

    def get(self, name):
        return self._kind.resolve_attr(name, self._data, self._repo)

    def set(self, item, value):
        self._data[item] = value

    def dump(self):
        return self.kind.dump(self)

    def __repr__(self):
        return json.dumps({self.ref: self._data})

    def __getattr__(self, item):
        return self.get(item)

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, item, value):
        self.set(item, value)

    def __iter__(self):
        return iter(self._data.keys())

    def items(self):
        for name in self._data:
            yield (name, self.get(name))


class RelationList(object):
    def __init__(self, parent, name, items):
        self._parent = parent
        self._items = items
        self._name = name

    @property
    def value(self):
        return self.required

    @property
    def required(self):
        if self._items is None:
            raise UnknownKindObjectRelationException(
                'Required list was not found: {0}.{1}'
                .format(self.parent.ref, self._name))
        return self._items

    def get_tag(self, tag):
        for item in self.required:
            if item.tag == tag:
                return Relation(self._parent, self._name, item)
        return Relation(self._parent, self._name, None)

    def __len__(self):
        return len(self.required)

    def __iter__(self):
        for item in self.required:
            yield Relation(self._parent, self._name, item)

    def __contains__(self, tag):
        return len(item for item in self.required if item.tag == tag) > 0

    def __bool__(self):
        return self._items is not None

    def __nonzero__(self):
        return self.__bool__()

    def __getitem__(self, item):
        return self.get_tag(item)


class Relation(object):
    def __init__(self, parent, name, value):
        self._parent = parent
        self._value = value
        self._name = name

    def __getitem__(self, item):
        return self.required.__getitem__(item)

    def __getattr__(self, name):
        return self.required.__getattr__(name)

    @property
    def value(self):
        return self._value

    @property
    def required(self):
        if self._value is None:
            raise UnknownKindObjectRelationException(
                'Required value was not found: {0}.{1}'
                .format(self.parent.ref, self._name))
        return self._value

    def __bool__(self):
        return self._value is not None

    def __nonzero__(self):
        return self.__bool__()


class PyautoException(Exception):
    pass


class DuplicateKindObjectException(PyautoException):
    def __init__(self, kind=None, tag=None, kind_tag=None):
        if kind_tag:
            data = kind_tag
        elif kind and tag:
            data = '/'.join([kind, tag])
        else:
            data = 'invalid tag'
        msg = 'Duplicate object: {0}'.format(data)
        super(DuplicateKindObjectException, self).__init__(msg)


class UnknownKindException(PyautoException):
    def __init__(self, kind):
        msg = 'Unknown kind: {0}'.format(kind)
        super(UnknownKindException, self).__init__(msg)


class UnknownPackageException(PyautoException):
    def __init__(self, package):
        msg = 'Unknown package: {0}'.format(package)
        super(UnknownPackageException, self).__init__(msg)


class UnknownKindObjectRelationException(PyautoException):
    pass


class UnknownKindObjectException(PyautoException):
    def __init__(self, kind=None, tag=None, kind_tag=None, value=None):
        if value is not None:
            data = value
        elif kind_tag:
            data = kind_tag
        elif kind and tag:
            data = '/'.join([kind, tag])
        else:
            data = '<unknown>'
        msg = 'Unknown object: {0}'.format(data)
        super(UnknownKindObjectException, self).__init__(msg)


class InvalidKindException(PyautoException):
    pass


class InvalidKindObjectException(PyautoException):
    pass


class InvalidKindObjectReferenceException(PyautoException):
    def __init__(self, tag):
        msg = 'Invalid object tag: {0}'.format(tag)
        super(InvalidKindObjectReferenceException, self).__init__(msg)


class InvalidKindTaskReferenceException(PyautoException):
    def __init__(self, ref):
        msg = 'Invalid task reference: {0}'.format(ref)
        super(InvalidKindTaskReferenceException, self).__init__(msg)


class InvalidKindAttributeDetailException(PyautoException):
    def __init__(self, defstr):
        msg = 'Invalid kind definition string: {0}'.format(defstr)
        super(InvalidKindAttributeDetailException, self).__init__(msg)


class UnknownTaskSequenceTypeException(PyautoException):
    pass


class UnknownTaskSequenceException(PyautoException):
    pass


class UnknownKindObjectTaskException(PyautoException):
    pass


class KindObjectAttributeException(PyautoException):
    pass


class InvalidQueryException(PyautoException):
    pass


class InvalidKindObjectTaskException(PyautoException):
    pass


class InvalidKindObjectTaskInvocationException(PyautoException):
    pass


class InvalidTaskSequenceInvocationException(PyautoException):
    pass


class KindObjectRelationException(PyautoException):
    pass


class InvalidQueryException(PyautoException):
    pass


class InvalidTaskArgumentException(PyautoException):
    pass
