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
        """
        login: {dep:[na1],app:[web]}
        """
        results = []
        for name, kind in self.items():
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

    def get(self, item):
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

    def add_kind(self, kind):
        if not isinstance(kind, Kind):
            kind = deepcopy(kind)
            kind = Kind(self, kind)
        kind.set_repo(self)
        if kind.name not in self._data:
            self._data[kind.name] = KindObjects(self, kind)
        return self

    def get_kind(self, kind):
        self.assert_kind(kind)
        return self._data[str(kind)].kind

    def remove_kind(self, kind):
        if kind.name in self._data:
            del self._data[kind.name]
            return True
        return False

    def add(self, obj):
        if not isinstance(obj, KindObject):
            obj = deepcopy(obj)
            obj = KindObject(self, obj)
        obj.set_repo(self)
        self.assert_kind(obj.kind.name)
        self._data[obj.kind.name].add(obj)
        return self

    def remove(self, obj):
        self.assert_kind(obj.kind.name)
        self._data[obj.kind.name].remove(obj)

    def parse_kinds(self, data):
        data = yamlutil.load_dict(data)
        return self.load_kinds(data)

    def load_kinds(self, data):
        data = deepcopy(data)
        for kind in data:
            self.add_kind(kind)
        for kindobjs in self._data.values():
            kindobjs.kind.load_relations()
        return self

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


class KindDefinition(object):
    name = None
    required = True
    list = False

    def __init__(self, key):
        if not isinstance(key, six.string_types):
            raise InvalidKindDefinitionException(key)
        parts = re.split('\s+', key)
        for i, part in enumerate(parts):
            if 0 == i:
                self.name = part
            elif 'optional' == part:
                self.required = False
            elif 'list' == part:
                self.list = True

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class AttributeDefinition(object):
    parsers = {
        'string': six.text_type,
        'path': os.path.abspath,
        'list': list,
        'map': OrderedDict,
        'reference': Reference,
        'relpath': 'path',
        'url': lambda uri: uriutil.format(**uriutil.parse(uri)),
        'int': int,
        'float': float,
        'envvar': os.getenv,
        'json': json.loads,
        'yaml': yamlutil.load_dict,
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


class Kind(object):
    def __init__(self, repo, kind):
        self._repo = repo
        self._kind = KindDefinition(kind['kind'])
        kind['attributes'] = OrderedDict([
            (name, AttributeDefinition(self, name, a))
            for name, a in kind.get('attributes', {}).items()
        ])
        kind['relations'] = OrderedDict([
            (name, KindDefinition(k))
            for name, k in kind.get('relations', {}).items()
        ])
        self._data = kind
        self._relations = None
        self._tasks = KindTasks(self, kind.get('tasks', []))

    @property
    def name(self):
        return str(self._kind)

    @property
    def tasks(self):
        return self._tasks

    def set_repo(self, repo):
        self._repo = repo
        return self

    def __repr__(self):
        return str(self._data)

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __getitem__(self, item):
        return self._data.get(item, None)

    def __setitem__(self, item, value):
        self._data[item] = value

    def __contains__(self, item):
        return item in self._data

    def load_relations(self):
        self._relations = OrderedDict([
            (name, self._repo.get_kind(kind))
            for name, kind in self._data['relations'].items()
        ])
        return self

    def validate_object(self, obj):
        for name, attr in self._data['attributes'].items():
            obj[name] = attr.get_attribute(obj)
        return obj

    def get_class(self):
        if 'class' not in self:
            return Config
        parts = self['class'].split('.')
        module_name = '.'.join(parts[:-1])
        class_name = parts[-1]
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    def wrap_object(self, obj):
        return self.get_class()(obj)

    def get_module(self):
        return importlib.import_module(self['module'])


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
            raise DuplicateObjectException(kind_tag=obj.get_id())
        self._items[obj.tag] = obj
        return self

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
        self._data = self._kind.wrap_object(obj)

    @property
    def tag(self):
        return self['tag']

    @property
    def kind(self):
        return self._kind

    @property
    def data(self):
        return self._data

    def validate(self):
        self._kind.validate_object(self._data)
        return self._data

    def set_repo(self, repo):
        self._repo = repo
        return self

    def __repr__(self):
        return ''.join(['<', self.__class__.__name__, ' ', self.get_id(), ' ',
                        str(self._data), '>'])

    def __getitem__(self, item):
        return self._data.get(item)

    def __setitem__(self, item, value):
        self._data.set(item, value)

    def items(self):
        return self._data.items()

    def __iter__(self):
        return iter(self._data.keys())

    def get_id(self):
        return '/'.join([self.kind.name, self.tag])

    def invoke(self, args, **kwargs):
        if len(kwargs) > 0:
            args = {args: kwargs}
        return self._kind.tasks.invoke(self, args)


class Config(object):
    def __init__(self, data):
        self._data = data

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self._data)

    def __getattr__(self, item):
        return self.get(item)

    def __getitem__(self, item):
        return self.get(item)

    def __setitem__(self, item, value):
        self.set(item, value)

    def __contains__(self, item):
        return item in self._data

    def get(self, item, default=None):
        return self._data.get(item, default)

    def set(self, item, value):
        self._data[item] = value

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()


class PyautoException(Exception):
    pass


class DuplicateObjectException(PyautoException):
    def __init__(self, kind=None, tag=None, kind_tag=None):
        if kind_tag:
            data = kind_tag
        elif kind and tag:
            data = '/'.join([kind, tag])
        else:
            data = 'invalid tag'
        msg = 'Duplicate object: {0}'.format(data)
        super(DuplicateObjectException, self).__init__(msg)


class UnknownKindException(PyautoException):
    def __init__(self, kind):
        msg = 'Unknown kind: {0}'.format(kind)
        super(UnknownKindException, self).__init__(msg)


class UnknownKindObjectException(PyautoException):
    def __init__(self, kind=None, tag=None, kind_tag=None):
        if kind_tag:
            data = kind_tag
        elif kind and tag:
            data = '/'.join([kind, tag])
        else:
            data = '<unknown>'
        msg = 'Unknown object: {0}'.format(data)
        super(UnknownKindObjectException, self).__init__(msg)


class InvalidKindObjectReferenceException(PyautoException):
    def __init__(self, tag):
        msg = 'Invalid object tag: {0}'.format(tag)
        super(InvalidKindObjectReferenceException, self).__init__(msg)


class InvalidKindDefinitionException(PyautoException):
    def __init__(self, defstr):
        msg = 'Invalid kind definition string: {0}'.format(defstr)
        super(InvalidKindDefinitionException, self).__init__(msg)


class UnknownTaskSequenceTypeException(PyautoException):
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
