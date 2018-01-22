import os, shutil
from unittest import TestCase
from pyauto.core import deploy
from pyauto.local import config

dirname = os.path.dirname(os.path.abspath(__file__))
local = deploy.Command(os.path.join(dirname, 'config.yml'), [])\
    .config.local


def setUpModule():
    local.init_workspace()


def tearDownModule():
    shutil.rmtree(local.workspace_dir)


class TestConfigLocal(TestCase):
    def test_init_workspace(self):
        local.init_workspace()

    def test_get_template_file(self):
        filename = local.get_template_file('example.j2')
        expected = os.path.join(dirname, 'templates/example.j2')
        self.assertEqual(filename, expected)

    def test_get_workspace_path(self):
        filename = local.get_workspace_path('example.j2')
        expected = os.path.join(dirname, 'workspace/example.j2')
        self.assertEqual(filename, expected)

    def test_get_destination(self):
        dst = local.get_destination('abc')
        self.assertIsInstance(dst, config.Destination)
        self.assertEqual(dst.id, 'abc')

    def test_get_source(self):
        src = local.get_source('project')
        self.assertIsInstance(src, config.Source)
        self.assertEqual(src.id, 'project')

    def test_copytree(self):
        local.copytree('project', 'abc')
        tree_source = os.path.join(dirname, 'sources/tree1/test.txt')
        tree_dest = os.path.join(dirname, 'workspace/tree1/test.txt')
        self.assertTrue(os.path.isfile(tree_source))
        self.assertTrue(os.path.isfile(tree_dest))

    def test_rmtree(self):
        self.test_copytree()
        local.rmtree('abc')
        tree_dest = os.path.join(dirname, 'workspace/tree1/test.txt')
        self.assertFalse(os.path.isfile(tree_dest))

class TestConfigLocalSource(TestCase):
    def test_get_path(self):
        tree_source = os.path.join(dirname, 'sources/tree1')
        self.assertEqual(tree_source, local.get_source('project').get_path())


class TestConfigLocalDestination(TestCase):
    def test_get_path(self):
        tree_dest = os.path.join(dirname, 'workspace/tree1')
        self.assertEqual(tree_dest, local.get_destination('abc').get_path())

    def test_copytree(self):
        local.get_destination('abc').copytree()
        tree_dest = os.path.join(dirname, 'workspace/tree1/test.txt')
        self.assertTrue(os.path.isfile(tree_dest))

    def test_copytree(self):
        dest = local.get_destination('abc')
        dest.copytree()
        dest.rmtree()
        tree_dest = os.path.join(dirname, 'workspace/tree1')
        self.assertFalse(os.path.isdir(tree_dest))

