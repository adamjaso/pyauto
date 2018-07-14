import os
import sys
import six
from copy import deepcopy
from collections import OrderedDict
from unittest import TestCase
from pyauto.core import objects
from pyauto.util import yamlutil

kinds_ = """
- kind: test.Region
  module: test.test_objects
  attributes:
    url: url
    user: string
    password: string
  tasks:
  - login
- kind: test.App
  module: test.test_objects
  attributes:
    org: string
    space: string
  relations:
    source: test.Directory
- kind: test.RegionApp
  module: test.test_objects
  relations:
    app: test.App
    region: test.Region
    destination: test.Directory
  tasks:
  - deploy
- kind: test.Directory
  module: test.test_objects
  attributes:
    name: string
  relations:
    source: test.Directory optional
  tasks:
  - rmtree
  - copytree
  - render_templates
"""
kinds_ = yamlutil.load_dict(kinds_)

tasks_ = """
regions:
  '{reg: test.Region}':
    'login':
    - 'cmd:test.Region.login {{reg.tag}}'
apps:
  '{reg: test.Region, app: test.App}':
    'copy':
    - 'cmd:test.Directory.copytree {{reg.tag}}_{{app.tag}}'
    'remove':
    - 'cmd:test.Directory.rmtree {{reg.tag}}_{{app.tag}}'
    'render':
    - 'cmd:test.Directory.render_templates {{reg.tag}}_{{app.tag}}'
    'deploy':
    - 'task:regions.login'
    - 'task:apps.remove'
    - 'task:apps.copy'
    - 'task:apps.render'
    - 'cmd:test.RegionApp.deploy {{reg.tag}}_{{app.tag}}'
"""
tasks_ = yamlutil.load_dict(tasks_)

objects_ = """
tag: r1
kind: test.Region
url: http://r1.localhost
user: admin
password: r1-pa$$word
---
tag: r2
kind: test.Region
url: http://r2.localhost
user: admin
password: r2-passw0rd
---
tag: web
kind: test.Directory
name: ./web
---
tag: api
kind: test.Directory
name: ./api
---
tag: web
kind: test.App
org: me
space: myproject
source: web
---
tag: api
kind: test.App
org: me
space: myproject
source: api
---
tag: r1_web
kind: test.RegionApp
app: web
region: r1
destination: r1_web
---
tag: r1_api
kind: test.RegionApp
app: api
region: r1
destination: r1_api
---
tag: r2_web
kind: test.RegionApp
app: web
region: r2
destination: r2_web
---
tag: r2_api
kind: test.RegionApp
app: api
region: r2
destination: r2_api
---
tag: r1_web
kind: test.Directory
name: ./r1_web
source: ./web
---
tag: r1_api
kind: test.Directory
name: ./r1_api
source: ./api
---
tag: r2_web
kind: test.Directory
name: ./r2_web
source: ./web
---
tag: r2_api
kind: test.Directory
name: ./r2_api
source: ./api
"""
objects_ = list(yamlutil.load_dict(objects_, load_all=True))

test_kind = {
    'kind': 'test.TestKind',
    'module': 'test.test_objects',
    'class': 'test.test_objects.TestKind',
    'attributes': {
        'name': 'string',
    },
    'relations': {
#        'source': 'test.Directory',
    },
    'tasks': {
        '_test_task',
    },
}

test_object = {
    'tag': 'muhthing',
    'kind': 'test.TestKind',
    'name': 'sumpthun',
    'source': 'web'
}


class TestKind(objects.KindObject):
    pass


def login(region, **args):
    pass


def deploy(app, **args):
    pass


def rmtree(dir_, **args):
    pass


def copytree(dir_, **args):
    pass


def render_templates(dir_, **args):
    return 'rendered!'


def _test_task(test_task, **args):
    return '$$$_test_task_$$$'


class TaskSequenceArguments(TestCase):
    def setUp(self):
        self.r = objects.Repository()
        self.r.load_kinds(kinds_)
        self.ts = objects.TaskSequences(self.r, tasks_)

    def test_len(self):
        self.assertEqual(len(self.ts['apps.deploy'].args), 2)


class TaskSequences(TestCase):
    def setUp(self):
        self.r = objects.Repository()
        self.r.load_kinds(kinds_)
        self.ts = objects.TaskSequences(self.r, tasks_)

    def test_repo(self):
        self.assertIsInstance(self.ts.repo, objects.Repository)

    def test_get(self):
        seqs = self.ts.get('apps.deploy')
        self.assertIsInstance(seqs, objects.TaskSequence)
        seqs = self.ts['apps.deploy']
        self.assertIsInstance(seqs, objects.TaskSequence)

    def test_task_sequence(self):
        names = ['regions.login', 'apps.deploy', 'apps.copy', 'apps.remove',
                 'apps.render']
        for name, tsq in self.ts.items():
            self.assertIn(name, names)
            self.assertIsInstance(tsq.args, objects.TaskSequenceArguments)


class TaskSequence(TestCase):
    def setUp(self):
        self.r = objects.Repository()
        self.r.load_kinds(kinds_)
        self.r.load_objects(objects_)
        self.ts = objects.TaskSequences(self.r, tasks_)
        self.tsq = self.ts['apps.deploy']

    def test_parse_task_command(self):
        parts = self.tsq.parse_task('cmd:test.Directory.rmtree {{test}}')
        self.assertEqual(len(parts), 2)
        self.assertIsInstance(parts[0], objects.KindTask)
        self.assertListEqual(parts[1], ['{{test}}'])

    def test_parse_task_task(self):
        parts = self.tsq.parse_task('task:regions.login')
        self.assertEqual(len(parts), 1)
        self.assertIsInstance(parts[0], objects.TaskSequence)

    def test_parse_task_unknown(self):
        with self.assertRaises(objects.UnknownTaskSequenceTypeException) as \
                context:
            self.tsq.parse_task('abc:regions.login')
        self.assertEqual(str(context.exception), 'Unknown task type: abc')

    def test_resolve(self):
        expected = [
            ('test.Region.login', 'test.Region/r1'),
            ('test.Region.login', 'test.Region/r2'),
            ('test.Directory.rmtree', 'test.Directory/r1_web'),
            ('test.Directory.rmtree', 'test.Directory/r1_api'),
            ('test.Directory.rmtree', 'test.Directory/r2_web'),
            ('test.Directory.rmtree', 'test.Directory/r2_api'),
            ('test.Directory.copytree', 'test.Directory/r1_web'),
            ('test.Directory.copytree', 'test.Directory/r1_api'),
            ('test.Directory.copytree', 'test.Directory/r2_web'),
            ('test.Directory.copytree', 'test.Directory/r2_api'),
            ('test.Directory.render_templates', 'test.Directory/r1_web'),
            ('test.Directory.render_templates', 'test.Directory/r1_api'),
            ('test.Directory.render_templates', 'test.Directory/r2_web'),
            ('test.Directory.render_templates', 'test.Directory/r2_api'),
            ('test.RegionApp.deploy', 'test.RegionApp/r1_web'),
            ('test.RegionApp.deploy', 'test.RegionApp/r1_api'),
            ('test.RegionApp.deploy', 'test.RegionApp/r2_web'),
            ('test.RegionApp.deploy', 'test.RegionApp/r2_api'),
        ]
        tasks = []
        self.tsq.resolve({}, tasks)
        for i, parts in enumerate(tasks):
            kt, ko = parts
            kte, koe = expected[i]
            self.assertEqual(kt.name, kte)
            self.assertEqual(ko.get_id(), koe)


class Repository(TestCase):
    def setUp(self):
        self.repo = objects.Repository()
        self.repo.load_kinds(kinds_)
        self.repo.load_objects(objects_)

    def test_kinds(self):
        for k in self.repo.kinds:
            self.assertIsInstance(k, objects.Kind)

    def test_query_objs(self):
        objs = self.repo.query({'test.Directory': []}, resolve=True)
        for obj in objs['test.Directory']:
            self.assertIsInstance(obj, objects.KindObject)

    def test_query_tags(self):
        objs = self.repo.query({'test.Directory': []}, tag=True, resolve=True)
        self.assertDictEqual(objs, OrderedDict([
            ('test.Directory', [
                'web', 'api', 'r1_web', 'r1_api', 'r2_web', 'r2_api'])]))

    def test_query_tags(self):
        objs = self.repo.query({'test.Directory': []}, id=True)
        self.assertListEqual(objs, [
            'test.Directory/web', 'test.Directory/api',
            'test.Directory/r1_web', 'test.Directory/r1_api',
            'test.Directory/r2_web', 'test.Directory/r2_api'])

    def test_iter(self):
        count = 0
        for item in self.repo:
            self.assertIsInstance(item, objects.KindObject)
            count += 1
        self.assertEqual(len(self.repo), count)
        self.assertEqual(len(self.repo), len(objects_))

    def test_get_objects(self):
        dir_ = self.repo['test.Directory']
        self.assertIsInstance(dir_, objects.KindObjects)

    def test_get_object(self):
        obj = self.repo['test.Region/r1']
        self.assertIsInstance(obj, objects.KindObject)

    def test_add_kind(self):
        self.assertNotIn('test.TestKind', self.repo)
        self.repo.add_kind(test_kind)
        self.assertIn('test.TestKind', self.repo)

    def test_add_kind_duplicate(self):
        self.assertNotIn('test.TestKind', self.repo)
        self.repo.add_kind(test_kind)
        self.repo.add_kind(test_kind)

    def test_get_kind(self):
        self.repo.add_kind(test_kind)
        kind = self.repo.get_kind('test.TestKind')
        self.assertIsInstance(kind, objects.Kind)
        self.assertEqual(kind.name, 'test.TestKind')

    def test_remove_kind(self):
        self.repo.add_kind(test_kind)
        kind = self.repo.get_kind('test.TestKind')
        self.repo.remove_kind(kind)
        self.assertNotIn('test.TestKind', self.repo)

    def test_add(self):
        self.repo.add_kind(test_kind)
        self.assertNotIn('test.TestKind/muhthing', self.repo)
        self.repo.add(test_object)
        self.assertIn('test.TestKind/muhthing', self.repo)

    def test_remove(self):
        self.repo.add_kind(test_kind)
        self.repo.add(test_object)
        thing = self.repo['test.TestKind/muhthing']
        self.repo.remove(thing)
        self.assertNotIn('test.TestKind/muhthing', self.repo)


class Reference(TestCase):
    def test_init(self):
        ref = objects.Reference('test.TestKind/muhthing')
        self.assertEqual(ref.kind, 'test.TestKind')
        self.assertEqual(ref.tag, 'muhthing')

    def test_init_invalid(self):
        with self.assertRaises(objects.InvalidKindObjectReferenceException):
            objects.Reference(None)


class KindAttributeDetail(TestCase):
    def setUp(self):
        self.r = objects.Repository()
        self.r.load_kinds(kinds_)

    def test_init(self):
        def_ = objects.KindAttributeDetail(self.r, 'sources', 'test.Directory')
        self.assertEqual(def_.name, 'sources')
        self.assertEqual(def_.kind, 'test.Directory')
        self.assertTrue(def_.required)
        self.assertFalse(def_.list)

    def test_optional(self):
        def_ = objects.KindAttributeDetail(self.r, 'sources',
                                      'test.Directory optional')
        self.assertEqual(def_.name, 'sources')
        self.assertEqual(def_.kind, 'test.Directory')
        self.assertFalse(def_.required)
        self.assertFalse(def_.list)

    def test_list(self):
        def_ = objects.KindAttributeDetail(self.r, 'sources',
                                      'test.Directory list')
        self.assertEqual(def_.name, 'sources')
        self.assertEqual(def_.kind, 'test.Directory')
        self.assertTrue(def_.required)
        self.assertTrue(def_.list)

    def test_optional_list(self):
        def_ = objects.KindAttributeDetail(self.r, 'sources',
                                      'test.Directory optional list')
        self.assertEqual(def_.name, 'sources')
        self.assertEqual(def_.kind, 'test.Directory')
        self.assertFalse(def_.required)
        self.assertTrue(def_.list)

    def test_get_attribute_list(self):
        ok2 = deepcopy(test_kind)
        ok2['relations'] = {'sources': 'test.TestKind list'}
        to2 = deepcopy(test_object)
        to2['tag'] += '2'
        to2['sources'] = [test_object['tag']]
        self.r.add_kind(ok2)
        self.r.add(test_object)
        self.r.add(to2)

        def_ = objects.KindAttributeDetail(self.r, 'sources',
                                      'test.TestKind optional list')
        value = def_.get_attribute(to2)
        for item in value:
            self.assertIsInstance(item, TestKind)

    def test_get_attribute(self):
        ok2 = deepcopy(test_kind)
        ok2['relations'] = {'sources': 'test.TestKind'}
        to2 = deepcopy(test_object)
        to2['tag'] += '2'
        self.r.add_kind(ok2)

        def_ = objects.KindAttributeDetail(self.r, 'sources',
                                      'test.TestKind')
        self.r.add(test_object)
        to2_ = self.r.add(to2)
        print(to2_, to2)
        with self.assertRaises(objects.KindObjectAttributeException):
            def_.get_attribute(to2)
        self.r.remove(to2_)
        to2['sources'] = test_object['tag']
        self.r.add(to2)
        value = def_.get_attribute(to2)
        self.assertIsInstance(value, TestKind)


class AttributeDetail(TestCase):
    def setUp(self):
        self.r = objects.Repository()
        self.r.add_kind(test_kind)
        kind = self.r.get_kind('test.TestKind')
        self.def_ = objects.AttributeDetail(kind, 'name', 'string optional')

    def test_init(self):
        pass

    def test_resolve_parser(self):
        self.def_.resolve_parser('relpath')

    def test_parse(self):
        res = self.def_.parse({})
        self.assertIsInstance(res, six.text_type)
        self.assertEqual(res, '{}')

    def test_get_attribute(self):
        self.r.add(test_object)
        obj = self.r['test.TestKind/muhthing']
        res = self.def_.get_attribute(obj)
        self.assertEqual(res, 'sumpthun')


class Kind(TestCase):
    def setUp(self):
        self.r = objects.Repository()
        self.r.add_kind(test_kind)
        self.kind = self.r.get_kind('test.TestKind')

    def test_init(self):
        pass

    def test_name(self):
        pass

    def test_tasks(self):
        pass

    def test_set_repo(self):
        pass

    def test_getattr(self):
        pass

    def test_setitem(self):
        pass

    def test_getitem(self):
        pass

    def test_contains(self):
        pass

    def test_load_relations(self):
        pass

    def test_validate_object(self):
        pass

    def test_get_class(self):
        self.assertEqual(self.kind.get_class(), TestKind)

    def test_wrap_object(self):
        obj = self.kind.wrap_object(test_object)
        self.assertIsInstance(obj, TestKind)

    def test_get_module(self):
        self.assertEqual(sys.modules[__name__], self.kind.get_module())


class KindTasks(TestCase):
    def setUp(self):
        self.r = objects.Repository()
        self.r.add_kind(test_kind)
        self.r.add(test_object)
        self.kt = self.r.get_kind('test.TestKind').tasks

    def test_kind(self):
        self.assertIsInstance(self.kt.kind, objects.Kind)

    def test_contains(self):
        self.assertTrue(self.kt.__contains__('_test_task'))

    def test_getitem(self):
        kt = self.kt.__getitem__('_test_task')
        self.assertIsInstance(kt, objects.KindTask)
        self.assertEqual(kt.name, 'test.TestKind._test_task')

    def test_parse_args_dict(self):
        fname, fargs = self.kt.parse_args({'_test_task': {}})
        self.assertEqual(fname, '_test_task')
        self.assertDictEqual(fargs, {})

    def test_parse_args_str(self):
        fname, fargs = self.kt.parse_args('_test_task')
        self.assertEqual(fname, '_test_task')
        self.assertDictEqual(fargs, {})

    def test_invoke(self):
        obj = self.r['test.TestKind/muhthing']
        res = self.kt.invoke(obj, '_test_task')
        self.assertEqual(res, '$$$_test_task_$$$')


class KindTask(TestCase):
    def setUp(self):
        self.r = objects.Repository()
        self.r.add_kind(test_kind)
        self.r.add(test_object)
        self.obj = self.r['test.TestKind/muhthing']
        self.kt = self.r.get_kind('test.TestKind').tasks['_test_task']

    def test_init(self):
        pass

    def test_name(self):
        self.assertEqual('test.TestKind._test_task', self.kt.name)

    def test_module_name(self):
        self.assertEqual(__name__ + '._test_task', self.kt.module_name)

    def test_tasks(self):
        self.assertIsInstance(self.kt.tasks, objects.KindTasks)

    def test_invoke(self):
        res = self.kt.invoke(self.obj)
        self.assertEqual(res, '$$$_test_task_$$$')

    def test_call(self):
        res = self.kt(self.obj)
        self.assertEqual(res, '$$$_test_task_$$$')


class KindObjects(TestCase):
    def setUp(self):
        self.r = objects.Repository()
        self.r.add_kind(test_kind)
        self.kobjs = self.r['test.TestKind']

    def test_init(self):
        self.assertIsInstance(self.kobjs, objects.KindObjects)

    def test_query(self):
        self.r.add(test_object)
        for o in self.kobjs.query(['muhthing']):
            self.assertIsInstance(o, objects.KindObject)

    def test_add(self):
        self.assertNotIn('muhthing', self.kobjs)
        self.r.add(test_object)
        self.assertIn('muhthing', self.kobjs)

    def test_remove(self):
        self.r.add(test_object)
        obj = self.kobjs['muhthing']
        self.r.remove(obj)
        self.assertNotIn('muhthing', self.kobjs)

    def test_getitem(self):
        self.r.add(test_object)
        obj = self.kobjs['muhthing']
        self.assertIsInstance(obj, objects.KindObject)

    def test_contains(self):
        self.r.add(test_object)
        self.assertTrue('muhthing' in self.kobjs)

    def test_iter(self):
        self.r.add(test_object)
        for obj in self.kobjs:
            self.assertIsInstance(obj, objects.KindObject)

    def test_len(self):
        self.r.add(test_object)
        self.assertEqual(len(self.kobjs), 1)


class KindObject(TestCase):
    def setUp(self):
        self.r = objects.Repository()
        self.r.add_kind(test_kind)
        self.r.add(test_object)
        self.obj = self.r['test.TestKind/muhthing']
        self.kind = self.r.get_kind('test.TestKind')

    def test_tag(self):
        self.assertEqual(self.obj.tag, 'muhthing')

    def test_kind(self):
        self.assertEqual(self.obj.kind, self.kind)

    def test_validate(self):
        self.obj.validate()

    def test_getitem(self):
        self.assertEqual(self.obj['name'], 'sumpthun')

    def test_setitem(self):
        self.assertNotIn('key', self.obj._data)
        self.obj['key'] = 'abc'
        self.assertEqual(self.obj._data['key'], 'abc')

