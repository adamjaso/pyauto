import os
import re
import six
import json
import shlex
import jinja2
import itertools
import importlib
from copy import deepcopy
from pyauto.util import yamlutil
from pyauto.util import uriutil
from collections import OrderedDict


class TaskSequenceArguments(object):
    def __init__(self, repo, args):
        parts = yamlutil.load_dict(args)
        self._repo = repo
        self._kinds = []
        self._names = []
        for name, kindstr in parts.items():
            kind = self._repo.get_kind(kindstr)
            self._names.append(name)
            self._kinds.append(kind)

    def __len__(self):
        return len(self._kinds)

    def __getitem__(self, i):
        return (self._names[i], self._kinds[i])

    def items(self):
        for i in range(len(self)):
            yield self[i]

    def resolve(self, args, **options):
        results = []
        for name, kind in self.items():
            if not isinstance(args, (dict, OrderedDict)):
                raise InvalidTaskSequenceInvocationException(
                    'Invalid task sequence args: {0}'.format(args))
            result = self._repo.query({kind.name: args.get(name, [])},
                                      **options)
            if 'id' in options and 'tag' in options:
                results.append(result)
            else:
                results.append(next([row for row in val]
                                    for val in result.values()))
        return [OrderedDict(zip(self._names, row))
                for row in itertools.product(*results)]

    def render(self, template, args, **options):
        template = jinja2.Template(template)
        rows = self.resolve(args, **options)
        for varlist in rows:
            yield template.render(**varlist)


class TaskSequences(object):
    def __init__(self, repo, tasks):
        self._repo = repo
        self._tasks = OrderedDict()
        for group, definition in tasks.items():
            args = next(iter(definition.keys()))
            args = TaskSequenceArguments(repo, args)
            for task, sequence in next(iter(definition.values())).items():
                name = '.'.join([group, task])
                self._tasks[name] = TaskSequence(self, name, args, sequence)

    def items(self):
        return self._tasks.items()

    @property
    def repo(self):
        return self._repo

    def has(self, item):
        return item in self

    def get(self, item):
        if not self.has(item):
            raise UnknownTaskSequenceException('Unknown task sequence: {0}'
                                               .format(item))
        return self._tasks.get(item)

    def __getitem__(self, item):
        return self.get(item)

    def __contains__(self, item):
        return item in self._tasks


class TaskSequence(object):
    def __init__(self, tasks, name, args, sequence):
        self._tasks = tasks
        self._repo = tasks.repo
        self._name = name
        self._args = args
        self._sequence = sequence

    @property
    def args(self):
        return self._args

    def __repr__(self):
        return ''.join(['<', self.__class__.__name__, ' ', self._name, ' ',
                        hex(id(self)), '>'])

    def parse_task(self, command):
        parts = command.split(':')
        if len(parts) != 2:
            raise InvalidTaskSequenceInvocationException(
                'Invalid task sequence: {0}'.format(command))

        if 'cmd' == parts[0]:
            parts_ = shlex.split(parts[1])
            tmpls = parts_[1:]
            parts_ = parts_[0].split('.')
            kind = '.'.join(parts_[:-1])
            kind = self._repo.get_kind(kind)
            task = parts_[-1]
            return kind.tasks[task], tmpls

        elif 'task' == parts[0]:
            return (self._tasks.get(parts[1]),)

        else:
            raise UnknownTaskSequenceTypeException(
                'Unknown task type: {0}'.format(parts[0]))

    def invoke(self, args):
        tasks = []
        self.resolve(args, tasks)
        for kt, ko in tasks:
            kt.invoke(ko)

    def resolve(self, args, resolved):
        for task in self._sequence:
            parts = self.parse_task(task)
            if isinstance(parts[0], KindTask):
                kt, tmpls = parts
                tags = self._args.render(tmpls[0], args)
                kos = self._repo[kt.tasks.kind.name]
                for tag in tags:
                    ko = kos[tag]
                    resolved.append((kt, ko))
            elif isinstance(parts[0], TaskSequence):
                parts[0].resolve(args, resolved)
            else:
                raise UnknownTaskSequenceTypeException(
                    'Attempted to invoke unknown task type: {0}'
                    .format(parts[0]))


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

    def query(self, match, **options):
        if options.get('id', False):
            result = []
            for kindstr, tags in match.items():
                items = self.get(kindstr).query(tags, **options)
                result.extend([i for i in items])
            return result
        else:
            result = OrderedDict()
            for kindstr, tags in match.items():
                items = self.get(kindstr).query(tags, **options)
                if options.get('resolve', False):
                    items = [i for i in items]
                result[kindstr] = items
            return result

    def __repr__(self):
        return ''.join(['<', self.__class__.__name__, '\n  ', '\n  '.join([
            ' '.join([kind, str(objs)])
            for kind, objs in self._data.items()]), '>'])

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
        'string': six.text_type,
        'path': os.path.abspath,
        'envvar': os.getenv,
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
        return str(self._data)

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

    def get_class(self):
        if 'class' not in self:
            return KindAPI
        parts = self['class'].split('.')
        module_name = '.'.join(parts[:-1])
        class_name = parts[-1]
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    def has_class(self):
        return 'class' in self

    def wrap_object(self, obj):
        return self.get_class()(obj)

    def get_module(self):
        return importlib.import_module(self['module'])

    def has_module(self):
        return 'module' in self


class KindTasks(object):
    def __init__(self, kind, tasks):
        tasks = tasks or []
        self._kind = kind
        self._tasks = OrderedDict()
        for task in tasks:
            if isinstance(task, six.string_types):
                module = self._kind.get_module()
                if not hasattr(module, task):
                    raise UnknownKindObjectTaskException(
                        'Module task not found: {0}'.format(task))
                self._tasks[task] = KindTask(self, module, task)
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
        self._function = getattr(module, task)

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
        return self._function(obj, **args)

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

    @property
    def data(self):
        return self._items

    def query(self, tags, **options):
        for item in self._items.values():
            if not tags or item.tag in tags:
                if options.get('id'):
                    yield item.get_id()
                elif options.get('tag'):
                    yield item.tag
                else:
                    yield item

    @property
    def kind(self):
        return self._kind

    def assert_object(self, tag):
        if tag not in self._items:
            raise UnknownKindObjectException(self.kind.name, tag)

    def add(self, obj):
        if not isinstance(obj, KindObject):
            obj = KindObject(self._repo, obj)
        if obj.tag in self._items:
            raise DuplicateKindObjectException(kind_tag=obj.get_id())
        self._items[obj.tag] = obj
        return obj

    def remove(self, obj):
        if obj.tag in self._items:
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
                        str(self._items), '>'])


class KindObject(object):
    def __init__(self, repo, obj):
        self._repo = repo
        self._kind = repo.get_kind(obj['kind'])
        self._data = obj

    @property
    def api(self):
        return self._kind.wrap_object(self)

    @property
    def tag(self):
        return self['tag']

    @property
    def kind(self):
        return self._kind

    @property
    def data(self):
        return self._data

    def set_repo(self, repo):
        self._repo = repo
        return self

    def get(self, name):
        return self._kind.resolve_attr(name, self._data, self._repo)

    def set(self, item, value):
        self._data[item] = value

    def __repr__(self):
        return ''.join(['<', self.__class__.__name__, ' ', self.get_id(), ' ',
                        str(self._data), '>'])

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

    def get_id(self):
        return '/'.join([self.kind.name, self.tag])

    def invoke(self, args, **kwargs):
        if len(kwargs) > 0:
            args = {args: kwargs}
        return self._kind.tasks.invoke(self, args)


class KindAPI(object):
    def __init__(self, kind_object):
        self._kind_object = kind_object

    def __getitem__(self, name):
        self._kind_object.get(name)

    def __getattr__(self, name):
        return self._kind_object.get(name)

    def __setitem__(self, name, value):
        self._kind_object.set(name, value)


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
                .format(self.parent.get_id(), self._name))
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
        return len(_ for item in self.required if item.tag == tag) > 0

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
                .format(self.parent.get_id(), self._name))
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
