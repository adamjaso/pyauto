import os, shutil, six
from unittest import TestCase
from pyauto.core import api
from pyauto.local import config
from pyauto.util import yamlutil
from collections import OrderedDict

dirname = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
repo = api.Repository()
repo.load_packages(config.packages)
repo.load_file(__file__, 'config.yml')


cfg = repo['file.Config/main']


class Tmp(api.KindObject):
    pass


def setUpModule():
    global cfg
    cfg.init_workspace()


def tearDownModule():
    global cfg
    shutil.rmtree(cfg.get_path())


class Config(TestCase):
    def test_get_path(self):
        path = os.path.join(dirname, 'v2test')
        self.assertEqual(path, cfg.get_path())


class Directory(TestCase):
    def setUp(self):
        self.dir = repo['file.Directory/copy']

    def tearDown(self):
        self.dir.remove_dir()

    def test_get_path(self):
        self.assertEqual(self.dir.get_path(),
                         os.path.join(dirname, 'v2test/copied'))

    def test_remove_dir(self):
        self.dir.copy_dir()
        self.assertTrue(os.path.isdir(self.dir.get_path()))
        self.dir.remove_dir()
        self.assertTrue(not os.path.isdir(self.dir.get_path()))

    def test_copy_dir(self):
        self.dir.copy_dir()
        self.assertTrue(os.path.isdir(self.dir.get_path()))

    def test_load_packages(self):
        dir_ = repo['file.Directory/extrapackages']
        dir_.load_packages()
        self.assertIn('extra.Tmp', repo)
        repo.remove_package(repo.get_package('extra'))

    def test_load_objects(self):
        dir_ = repo['file.Directory/extrapackages']
        dir_.load_packages()
        dir_ = repo['file.Directory/extraobjects']
        dir_.load_objects()
        self.assertIn('extra.Tmp/loadabletmp', repo)
        repo.remove_package(repo.get_package('extra'))
        repo.remove(repo['file.File/loadablefile'])


class File(TestCase):
    def setUp(self):
        self.file = repo['file.File/firstfile']

    def tearDown(self):
        self.file.remove_file()

    def test_get_path(self):
        self.assertEqual(self.file.get_path(),
                         os.path.join(dirname, 'v2test/tasks2.yml'))

    def test_get_source_path(self):
        self.assertEqual(self.file.get_source_path(),
                         os.path.join(dirname, 'setup.py'))

    def test_remove_file(self):
        self.file.copy_file()
        self.assertTrue(os.path.isfile(self.file.get_path()))
        self.file.remove_file()
        self.assertTrue(not os.path.isfile(self.file.get_path()))

    def test_copy_file(self):
        self.file.copy_file()
        self.assertTrue(os.path.isfile(self.file.get_path()))

    def test_resolve_variables(self):
        f = repo['file.File/myrendered']
        data = f.resolve_variables()
        self.assertDictEqual(data, {'var1': 1, 'var2': 2})

    def test_render_template(self):
        f = repo['file.File/myrendered']
        self.assertTrue(not os.path.isfile(f.get_path()))
        f.render_template()
        self.assertTrue(os.path.isfile(f.get_path()))

    def test_load_packages(self):
        dir_ = repo['file.File/extrapackages']
        dir_.load_packages()
        self.assertIn('extra.Tmp', repo)
        repo.remove_package(repo.get_package('extra'))

    def test_load_objects(self):
        dir_ = repo['file.File/extrapackages']
        dir_.load_packages()
        dir_ = repo['file.File/extraobjects']
        dir_.load_objects()
        self.assertIn('extra.Tmp/loadabletmp', repo)
        repo.remove_package(repo.get_package('extra'))
        repo.remove(repo['file.File/loadablefile'])


class Variable(TestCase):
    def test_resolve(self):
        v = repo['file.Variable/myvar']
        data = v.resolve()
        self.assertDictEqual(data, {'var1': 1, 'var2': 2})

    def test_resolve_file(self):
        v = repo['file.Variable/myvarfile']
        data = v.resolve()
        self.assertDictEqual(OrderedDict([
            ('key1', 'val1'),
            ('key2', 'val2'),
            ('key3', ['val3', 'val4']),
            ('key4', OrderedDict([
                ('key5', 'val5'),
                ('key6', 'val6')]))]), data)

    def test_resolve_env(self):
        v = repo['file.Variable/myvarenv']
        self.assertDictEqual(v.resolve(), {'PWD': os.getcwd()})

    def test_resolve_variable(self):
        v = repo['file.Variable/myvarpointer']
        data = v.resolve()
        self.assertDictEqual(OrderedDict([
            ('key1', 'val1'),
            ('key2', 'val2'),
            ('key3', ['val3', 'val4']),
            ('key4', OrderedDict([
                ('key5', 'val5'),
                ('key6', 'val6')]))]), data)
        v = repo['file.Variable/myvarpointerkey4']
        self.assertDictEqual(
            OrderedDict([('key5', 'val5'), ('key6', 'val6')]), v.resolve())

    def test_resolve_function(self):
        v = repo['file.Variable/myvarfunc']
        data = v.resolve()
        self.assertDictEqual(OrderedDict([('abc', 123)]), data)


def varfunc(data):
    return yamlutil.load_dict(data)
