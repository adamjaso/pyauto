import os, shutil, six
from unittest import TestCase
from pyauto.core import deploy, config as core_config
from pyauto.local import config

dirname = os.path.dirname(os.path.abspath(__file__))
local = deploy.Command(os.path.join(dirname, 'config.yml'), [])\
    .config.local


def get_test_value():
    return 'foo'


def setUpModule():
    local.init_workspace()


def tearDownModule():
    shutil.rmtree(local.workspace_dir)


class Local(TestCase):
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
        self.assertEqual(dst.get_id(), 'abc')

    def test_get_source(self):
        src = local.get_source('project')
        self.assertIsInstance(src, config.Source)
        self.assertEqual(src.get_id(), 'project')

    def test_copytree(self):
        local.copytree('project', 'abc')
        tree_source = os.path.join(dirname, 'sources/tree1/test.txt')
        tree_dest = os.path.join(dirname, 'workspace/tree1/test.txt')
        ignore_dest = os.path.join(dirname, 'workspace/tree1/ignore.txt')
        self.assertTrue(os.path.isfile(tree_source))
        self.assertTrue(os.path.isfile(tree_dest))
        self.assertFalse(os.path.isfile(ignore_dest))

    def test_rmtree(self):
        self.test_copytree()
        local.rmtree('abc')
        tree_dest = os.path.join(dirname, 'workspace/tree1/test.txt')
        self.assertFalse(os.path.isfile(tree_dest))

    def test_get_source_path(self):
        filename = local.get_source_path('project', 'test.txt')
        self.assertTrue(filename.endswith('/tree1/test.txt'))

    def test_get_destination_path(self):
        filename = local.get_destination_path('abc', 'test.txt')
        self.assertTrue(filename.endswith('/tree1/test.txt'))


class LocalSource(TestCase):
    def test_get_path(self):
        tree_source = os.path.join(dirname, 'sources/tree1')
        self.assertEqual(tree_source, local.get_source('project').get_path())


class LocalDestination(TestCase):
    def setUp(self):
        self.dest = local.get_destination('abc')
        self.cleanup_template_destinations()

    def tearDown(self):
        self.cleanup_template_destinations()

    def cleanup_template_destinations(self):
        filenames = self.dest.get_template_destinations()
        for fn in filenames:
            if os.path.isfile(fn):
                os.remove(fn)

    def test_get_path(self):
        tree_dest = os.path.join(dirname, 'workspace/tree1')
        self.assertEqual(tree_dest, local.get_destination('abc').get_path())

    def test_copytree(self):
        self.dest.copytree()
        tree_dest = os.path.join(dirname, 'workspace/tree1/test.txt')
        self.assertTrue(os.path.isfile(tree_dest))

    def test_rmtree(self):
        dest = self.dest
        dest.copytree()
        dest.rmtree()
        tree_dest = os.path.join(dirname, 'workspace/tree1')
        self.assertFalse(os.path.isdir(tree_dest))

    def test_render_templates(self):
        dest = self.dest
        dest.render_templates()
        filenames = dest.get_template_destinations()
        for fn in filenames:
            self.assertTrue(os.path.isfile(fn))


class LocalTemplate(TestCase):
    def test_init(self):
        template = local.get_template('project_config')
        self.assertIsInstance(template, config.Template)
        self.assertIsInstance(template.variables, config.VariableList)

    def test_destination_filename(self):
        dest = local.get_destination('abc')
        template = dest.get_template('project_config')
        self.assertEqual(template.destination_filename, 'config.region.yml')
        template = dest.get_template('project_config_no_filename')
        self.assertEqual(template.destination_filename, 'example.yml')

    def test_template_filename(self):
        dest = local.get_destination('abc')
        template = dest.get_template('project_config')
        filename = template.template_filename
        self.assertEqual(filename, 'example.j2')
        template = local.get_template('project_config')
        filename = template.template_filename
        self.assertEqual(filename, 'example.j2')

    def test_render_template(self):
        dest = local.get_destination('abc')
        template = dest.get_template('project_config')
        data = template.render_template()
        expected = local.render_template(
            'example.j2',
            tag=os.getenv('HOME'),
            name=os.getenv('PWD'))
        self.assertEqual(data, expected)

    def test_get_context(self):
        dest = local.get_destination('abc')
        template = dest.get_template('project_config')
        data = template.get_context()
        expected = {'tag': os.getenv('HOME'),
                    'name': os.getenv('PWD'),
                    'id': os.getenv('PWD'),}
        self.assertDictEqual(data, expected)

        template = local.get_template('project_config')
        data = template.get_context()
        expected = {'id': os.getenv('PWD')}
        self.assertDictEqual(data, expected)


class LocalVariableList(TestCase):
    def test_init(self):
        dest = local.get_destination('abc')
        template = dest.get_template('project_config')
        self.assertIsInstance(len(template.variables), int)

    def test_get_context(self):
        template = local.get_template('project_config')

        data = template.variables.get_context({'id': 123})
        expected = {'id': 123}
        self.assertDictEqual(data, expected)

        data = template.variables.get_context({})
        expected = {'id': os.getenv('PWD')}
        self.assertDictEqual(data, expected)

        dest = local.get_destination('abc')
        template = dest.get_template('project_config')
        data = template.variables.get_context({'id': 123})
        expected = {'id': 123,
                    'tag': os.getenv('HOME'),
                    'name': os.getenv('PWD')}
        self.assertDictEqual(data, expected)

        expected = {'tag': os.getenv('HOME'),
                    'name': os.getenv('PWD')}
        data = template.variables.get_context({})
        self.assertDictEqual(data, expected)


class LocalVariable(TestCase):
    def test_get_env(self):
        dest = local.get_destination('abc')
        template = dest.get_template('project_config')
        for var in template.variables:
            if 'env' in var:
                self.assertIsInstance(var.get_env(), six.string_types)

    def test_get_resource(self):
        dest = local.get_destination('abc')
        template = dest.get_template('project_config_no_filename')
        for var in template.variables:
            if 'resource' in var:
                res = var.get_resource()
                if isinstance(res, core_config.Config):
                    self.assertIsInstance(res, core_config.Config)
                else:
                    self.assertIsInstance(res, six.string_types)
        # TODO: test local.get_template().variables

    def test_get_file(self):
        dest = local.get_destination('abc')
        template = dest.get_template('project_config_no_filename')
        for var in template.variables:
            if 'file' in var:
                val = var.get_file()
                if isinstance(val, six.string_types):
                    self.assertEqual(val, 'foo: bar\n')
                elif isinstance(val, dict):
                    self.assertDictEqual(val, {'foo': 'bar'})
        # TODO: test local.get_template().variables

    def test_get_function(self):
        dest = local.get_destination('abc')
        template = dest.get_template('project_config_no_filename')
        for var in template.variables:
            if 'function' in var:
                data = var.get_function()
                self.assertEqual(data, 'foo')

    def test_get_value(self):
       dest = local.get_destination('abc')
       template = dest.get_template('project_config_no_filename')
       for var in template.variables:
           if 'resource' in var and 'select' in var:
               data = var.get_value()
               self.assertDictEqual(data, {
                   'abc_filename': 'config.region.yml'
               })

