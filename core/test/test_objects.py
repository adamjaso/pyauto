import os
import sys
import six
from copy import deepcopy
from collections import OrderedDict
from unittest import TestCase
from pyauto.core import api
from pyauto.util import yamlutil

packages_ = """
- package: test
  version: 0.0.0
  dependencies:
  - test
  kinds:
  - kind: Region
    configs: test.test_objects.Region
    attributes:
      url: string
      user: string
      password: string
    tasks:
    - login
  - kind: App
    configs: test.test_objects.App
    attributes:
      org: string
      space: string
    relations:
      source: test.Directory
  - kind: RegionApp
    configs: test.test_objects.RegionApp
    relations:
      app: test.App
      region: test.Region
      destination: test.Directory
    tasks:
    - deploy
  - kind: Directory
    configs: test.test_objects.Directory
    attributes:
      name: string
    relations:
      source: test.Directory optional
    tasks:
    - rmtree
    - copytree
    - render_templates
"""
packages_ = yamlutil.load_dict(packages_)

tasks_ = """
regions:
  '{reg: test.Region}':
    'login':
    - 'cmd:test.Region.login {{reg.tag}}'
regions_with_group:
  '{reg: test.Region, __options__: {match: labels}}':
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
labels:
- region1
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


def get_test_kind(name=None, attributes=None, relations=None):
    return {
        'kind': name or 'TestKind',
        'configs': 'test.test_objects.TestKind',
        'attributes': attributes or {
            'name': 'string',
        },
        'relations': relations or {
        },
        'tasks': {
            '_test_task',
        },
    }


def get_test_package(package=None, kinds=None, attributes=None, relations=None):
    return {
        'package': package or 'test2',
        'version': '0.0.0',
        'dependencies': [],
        'kinds': [get_test_kind(kind, attributes, relations)
                  for kind in (kinds or ['TestKind'])]
    }


def get_test_object(package='test2', kind='TestKind', tag='muhthing', **kwargs):
    obj = {
        'tag': tag,
        'kind': '.'.join([package, kind]),
        'labels': kwargs.get('labels', []),
        'name': 'sumpthun',
        'source': 'web'
    }
    obj.update(kwargs)
    return obj


class Region(api.KindObject):
    def login(self, **kwargs):
        return 'login!'


class App(api.KindObject):
    pass


class RegionApp(api.KindObject):
    def deploy(self, **kwargs):
        pass


class Directory(api.KindObject):
    def rmtree(self, **kwargs):
        pass

    def copytree(self, **kwargs):
        pass

    def render_templates(self, **kwargs):
        pass


class TestKind(api.KindObject):
    def _test_task(self, **args):
        return '$$$_test_task_$$$'


class Package(TestCase):
    def setUp(self):
        self.r = api.Repository()
        self.r.load_packages(packages_)

    def test_name(self):
        test = self.r.get_package('test')
        self.assertEqual(test.name, 'test')

    def test_kinds(self):
        test = self.r.get_package('test')
        for kind in test.kinds:
            self.assertIsInstance(kind, api.Kind)
            self.assertEqual(kind.package.name, 'test')

    def test_repo(self):
        test = self.r.get_package('test')
        self.assertIsInstance(test.repo, api.Repository)

    def test_dependencies(self):
        test = self.r.get_package('test')
        for dep in test.dependencies:
            self.r.assert_package(dep)

    def test_get(self):
        test = self.r.get_package('test')
        self.assertEqual(test.get('version'), '0.0.0')

    def test_getitem(self):
        test = self.r.get_package('test')
        self.assertEqual(test['version'], '0.0.0')

    def test_getattr(self):
        test = self.r.get_package('test')
        self.assertEqual(test.version, '0.0.0')


class Repository(TestCase):
    def setUp(self):
        self.repo = api.Repository()
        self.repo.load_packages(packages_)
        self.repo.load_objects(objects_)

    def test_kinds(self):
        for k in self.repo.kinds:
            self.assertIsInstance(k, api.Kind)

    def test_query_objs(self):
        for obj in self.repo['test.Directory']:
            self.assertIsInstance(obj, api.KindObject)

    def test_query_tags(self):
        objs = [o.tag for o in self.repo['test.Directory']]
        self.assertListEqual(objs, [
            'web', 'api', 'r1_web', 'r1_api', 'r2_web', 'r2_api'])

    def test_query_tags2(self):
        objs = [o.ref for o in self.repo['test.Directory']]
        self.assertListEqual(objs, [
            'test.Directory/web', 'test.Directory/api',
            'test.Directory/r1_web', 'test.Directory/r1_api',
            'test.Directory/r2_web', 'test.Directory/r2_api'])

    def test_iter(self):
        count = 0
        for item in self.repo:
            self.assertIsInstance(item, api.KindObject)
            count += 1
        self.assertEqual(len(self.repo), count)
        self.assertEqual(len(self.repo), len(objects_))

    def test_get_objects(self):
        dir_ = self.repo['test.Directory']
        self.assertIsInstance(dir_, api.KindObjects)

    def test_get_object(self):
        obj = self.repo['test.Region/r1']
        self.assertIsInstance(obj, api.KindObject)

    def test_get_kind(self):
        test_package = get_test_package()
        self.repo.add_package(test_package)
        kind = self.repo.get_kind('test2.TestKind')
        self.assertIsInstance(kind, api.Kind)
        self.assertEqual(kind.name, 'test2.TestKind')

    def test_add(self):
        test_package = get_test_package()
        self.repo.add_package(test_package)
        self.assertNotIn('test2.TestKind/muhthing', self.repo)
        self.repo.add(get_test_object('test2', 'TestKind', 'muhthing'))
        self.assertIn('test2.TestKind/muhthing', self.repo)

    def test_remove(self):
        test_package = get_test_package()
        self.repo.add_package(test_package)
        self.repo.add(get_test_object('test2', 'TestKind', 'muhthing'))
        thing = self.repo['test2.TestKind/muhthing']
        self.repo.remove(thing)
        self.assertNotIn('test2.TestKind/muhthing', self.repo)

    def test_invoke_kind_task(self):
        data = self.repo.invoke_kind_task(
            'test.Region', 'r1', 'login', None)
        self.assertIsInstance(data, OrderedDict)
        for k in ['task', 'obj', 'time', 'duration', 'result']:
            self.assertIn(k, data)

    def test_load_file(self):
        fn = os.path.dirname(os.path.abspath(__file__))
        fn = os.path.join(fn, 'objects-example', 'objects.yml')
        with self.assertRaises(api.DuplicateKindObjectException):
            self.repo.load_file(fn)


class Reference(TestCase):
    def test_init(self):
        ref = api.Reference('test2.TestKind/muhthing')
        self.assertEqual(ref.kind, 'test2.TestKind')
        self.assertEqual(ref.tag, 'muhthing')

    def test_init_invalid(self):
        with self.assertRaises(api.InvalidKindObjectReferenceException):
            api.Reference(None)


class KindAttributeDetail(TestCase):
    def setUp(self):
        self.r = api.Repository()
        self.r.load_packages(packages_)

    def test_init(self):
        test_package = self.r.get_package('test')
        def_ = api.KindAttributeDetail(
            test_package, 'sources', 'test.Directory')
        self.assertEqual(def_.name, 'sources')
        self.assertEqual(def_.kind, 'test.Directory')
        self.assertTrue(def_.required)
        self.assertFalse(def_.list)

    def test_optional(self):
        test_package = self.r.get_package('test')
        def_ = api.KindAttributeDetail(
            test_package, 'sources', 'test.Directory optional')
        self.assertEqual(def_.name, 'sources')
        self.assertEqual(def_.kind, 'test.Directory')
        self.assertFalse(def_.required)
        self.assertFalse(def_.list)

    def test_list(self):
        test_package = self.r.get_package('test')
        def_ = api.KindAttributeDetail(
            test_package, 'sources', 'test.Directory list')
        self.assertEqual(def_.name, 'sources')
        self.assertEqual(def_.kind, 'test.Directory')
        self.assertTrue(def_.required)
        self.assertTrue(def_.list)

    def test_optional_list(self):
        test_package = self.r.get_package('test')
        def_ = api.KindAttributeDetail(
            test_package, 'sources', 'test.Directory optional list')
        self.assertEqual(def_.name, 'sources')
        self.assertEqual(def_.kind, 'test.Directory')
        self.assertFalse(def_.required)
        self.assertTrue(def_.list)

    def test_get_attribute_list(self):
        test_package = get_test_package()
        ok2 = get_test_package(
            package='test3',
            relations={'sources': 'test2.TestKind list'})
        test_object = get_test_object()
        to2 = get_test_object(
            package='test3',
            kind='TestKind',
            tag='muhthing2',
            sources=[test_object['tag']])
        self.r.add_package(test_package)
        self.r.add_package(ok2)
        self.r.add(test_object)
        self.r.add(to2)

        test_package = self.r.get_package('test')
        def_ = api.KindAttributeDetail(
            test_package, 'sources', 'test2.TestKind list')
        value = def_.get_attribute(to2, self.r)
        for item in value:
            self.assertIsInstance(item.value, api.KindObject)

    def test_get_attribute(self):
        ok2 = get_test_package(
            package='test3',
            relations={'sources': 'test2.TestKind'})
        to2 = get_test_object(tag='muhthing2')
        test_package = get_test_package()
        test_object = get_test_object()

        self.r.add_package(ok2)
        self.r.add_package(test_package)
        self.r.add(test_object)

        to2_ = self.r.add(to2)
        test_package = self.r.get_package('test')
        def_ = api.KindAttributeDetail(
            test_package, 'sources', 'test2.TestKind')
        with self.assertRaises(api.KindObjectAttributeException):
            def_.get_attribute(to2, self.r)
        self.r.remove(to2_)
        to2['sources'] = test_object['tag']
        self.r.add(to2)
        value = def_.get_attribute(to2, self.r)
        self.assertIsInstance(value.required, api.KindObject)


class AttributeDetail(TestCase):
    def setUp(self):
        test_package = get_test_package()
        self.r = api.Repository()
        self.r.add_package(test_package)
        kind = self.r.get_kind('test2.TestKind')
        self.def_ = api.AttributeDetail(kind, 'name', 'string optional')

    def test_init(self):
        pass

    def test_resolve_parser(self):
        self.def_.resolve_parser('path')

    def test_parse(self):
        res = self.def_.parse({})
        self.assertIsInstance(res, six.text_type)
        self.assertEqual(res, '{}')

    def test_get_attribute(self):
        test_object = get_test_object()
        self.r.add(test_object)
        obj = self.r['test2.TestKind/muhthing']
        res = self.def_.get_attribute(obj)
        self.assertEqual(res, 'sumpthun')


class Kind(TestCase):
    def setUp(self):
        test_package = get_test_package()
        self.r = api.Repository()
        self.r.add_package(test_package)
        self.kind = self.r.get_kind('test2.TestKind')

    def test_init(self):
        pass

    def test_name(self):
        self.assertEqual(self.kind.name, 'test2.TestKind')

    def test_tasks(self):
        self.assertIsInstance(self.kind.tasks, api.KindTasks)

    def test_getattr(self):
        pass

    def test_getitem(self):
        pass

    def test_contains(self):
        pass


class KindTasks(TestCase):
    def setUp(self):
        test_package = get_test_package()
        test_object = get_test_object()
        self.r = api.Repository()
        self.r.add_package(test_package)
        self.r.add(test_object)
        self.kt = self.r.get_kind('test2.TestKind').tasks

    def test_kind(self):
        self.assertIsInstance(self.kt.kind, api.Kind)

    def test_contains(self):
        self.assertTrue(self.kt.__contains__('_test_task'))

    def test_getitem(self):
        kt = self.kt.__getitem__('_test_task')
        self.assertIsInstance(kt, api.KindTask)
        self.assertEqual(kt.name, 'test2.TestKind._test_task')

    def test_parse_args_dict(self):
        fname, fargs = self.kt.parse_args({'_test_task': {}})
        self.assertEqual(fname, '_test_task')
        self.assertDictEqual(fargs, {})

    def test_parse_args_str(self):
        fname, fargs = self.kt.parse_args('_test_task')
        self.assertEqual(fname, '_test_task')
        self.assertDictEqual(fargs, {})

    def test_invoke(self):
        obj = self.r['test2.TestKind/muhthing']
        res = self.kt.invoke(obj, '_test_task')
        self.assertEqual(res, '$$$_test_task_$$$')


class KindTask(TestCase):
    def setUp(self):
        self.r = api.Repository()
        test_package = get_test_package()
        test_object = get_test_object()
        self.r.add_package(test_package)
        self.r.add(test_object)
        self.obj = self.r['test2.TestKind/muhthing']
        self.kt = self.r.get_kind('test2.TestKind').tasks['_test_task']

    def test_init(self):
        pass

    def test_name(self):
        self.assertEqual('test2.TestKind._test_task', self.kt.name)

    def test_module_name(self):
        self.assertEqual('TestKind._test_task', self.kt.module_name)

    def test_tasks(self):
        self.assertIsInstance(self.kt.tasks, api.KindTasks)

    def test_invoke(self):
        res = self.kt.invoke(self.obj)
        self.assertEqual(res, '$$$_test_task_$$$')

    def test_call(self):
        res = self.kt(self.obj)
        self.assertEqual(res, '$$$_test_task_$$$')


class KindObjects(TestCase):
    def setUp(self):
        test_package = get_test_package()
        self.r = api.Repository()
        self.r.add_package(test_package)
        self.kobjs = self.r['test2.TestKind']

    def test_init(self):
        self.assertIsInstance(self.kobjs, api.KindObjects)

    def test_query(self):
        test_object = get_test_object()
        self.r.add(test_object)
        for o in self.kobjs.query({'tags': ['muhthing']}):
            self.assertIsInstance(o, TestKind)

    def test_add(self):
        test_object = get_test_object()
        self.assertNotIn('muhthing', self.kobjs)
        self.r.add(test_object)
        self.assertIn('muhthing', self.kobjs)

    def test_labels(self):
        test_object = get_test_object(labels=['region1'])
        self.r.add(test_object)
        self.assertIn('region1', self.kobjs._labels)

    def test_query_labels(self):
        test_object = get_test_object(labels=['region1'])
        self.r.add(test_object)
        print(self.r)
        res = self.kobjs.query_labels(['region1'])
        for obj in res:
            break
        else:
            raise api.PyautoException('object not found')

    def test_remove(self):
        test_object = get_test_object()
        self.r.add(test_object)
        obj = self.kobjs['muhthing']
        self.r.remove(obj)
        self.assertNotIn('muhthing', self.kobjs)

    def test_getitem(self):
        test_object = get_test_object()
        self.r.add(test_object)
        obj = self.kobjs['muhthing']
        self.assertIsInstance(obj, api.KindObject)

    def test_contains(self):
        test_object = get_test_object()
        self.r.add(test_object)
        self.assertTrue('muhthing' in self.kobjs)

    def test_iter(self):
        test_object = get_test_object()
        self.r.add(test_object)
        for obj in self.kobjs:
            self.assertIsInstance(obj, api.KindObject)

    def test_len(self):
        test_object = get_test_object()
        self.r.add(test_object)
        self.assertEqual(len(self.kobjs), 1)


class KindObject(TestCase):
    def setUp(self):
        test_package = get_test_package()
        test_object = get_test_object()
        self.r = api.Repository()
        self.r.add_package(test_package)
        self.r.add(test_object)
        self.obj = self.r['test2.TestKind/muhthing']
        self.kind = self.r.get_kind('test2.TestKind')

    def test_tag(self):
        self.assertEqual(self.obj.tag, 'muhthing')

    def test_kind(self):
        self.assertEqual(self.obj.kind, self.kind)

    def test_getitem(self):
        self.assertEqual(self.obj['name'], 'sumpthun')

    def test_getitem_resolve_relations(self):
        ok2 = get_test_package('test3', relations={'sources': 'test2.TestKind list'})
        self.r.add_package(ok2)

        test_object = get_test_object()
        to2 = get_test_object('test3', 'TestKind', 'muhthing2')
        to2['sources'] = [test_object['tag']]
        self.r.add(to2)
        obj2 = self.r[to2['kind']][to2['tag']]
        for src in obj2.sources:
            self.assertIsInstance(src.value, api.KindObject)
        for src in obj2['sources']:
            self.assertIsInstance(src.value, api.KindObject)

    def test_setitem(self):
        self.assertNotIn('key', self.obj._data)
        self.obj['key'] = 'abc'
        self.assertEqual(self.obj._data['key'], 'abc')


class RelationList(TestCase):
    def setUp(self):
        self.r = api.Repository()
        test_package = get_test_package()
        test_kind = get_test_kind()
        test_object = get_test_object()
        self.r.add_package(test_package)
        self.r.add(test_object)

        ok2 = get_test_package('test3', relations={'sources': 'test2.TestKind list'})
        self.r.add_package(ok2)

        to2 = deepcopy(test_object)
        to2['tag'] += '2'
        to2['kind'] = 'test3.TestKind'
        to2['sources'] = [test_object['tag']]
        self.r.add(to2)

        self.obj2 = self.r['test3.TestKind/muhthing2']

    def test_init(self):
        self.assertIsInstance(self.obj2.sources, api.RelationList)

    def test_value(self):
        self.assertIsInstance(self.obj2.sources.value, list)

    def test_get_tag(self):
        self.assertIsInstance(self.obj2.sources.get_tag('muhthing'),
                              api.Relation)

    def test_getitem(self):
        rel = self.obj2.sources['muhthing']
        self.assertIsInstance(rel, api.Relation)
        muh = rel.required
        self.assertEqual(muh.ref, 'test2.TestKind/muhthing')

    def test_len(self):
        self.assertEqual(len(self.obj2.sources), 1)

    def test_iter(self):
        for item in self.obj2.sources:
            self.assertIsInstance(item, api.Relation)
