from __future__ import print_function
import os
from unittest import TestCase
import test.example.commands as example_commands
import test.example.config as example_config
from pyauto import yamlutil, config as pyauto_config


config_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'example/config.example.yml')
with open(config_file) as f:
    config_str = f.read().strip()
config = pyauto_config.load(config_file)


class TestConfig(TestCase):
    def test_instance(self):
        self.assertIsInstance(config, pyauto_config.Config)

    def test_registered_module(self):
        self.assertIn('example', pyauto_config._config_classes)
        self.assertEqual(pyauto_config._config_classes['example'],
                         example_config.Example.wrap)
        self.assertIsInstance(config.example, example_config.Example)
        self.assertIsInstance(config['example'], example_config.Example)

    def test_unregistered_module(self):
        self.assertNotIn('example2', pyauto_config._config_classes)
        self.assertIsInstance(config.example2, dict)
        self.assertIsInstance(config['example2'], dict)

    def test_to_dict(self):
        config_dict = config.to_dict()
        config_yaml = yamlutil.dump_dict(config_dict).strip()
        self.assertEqual(config_yaml, config_str)

    def test_get_resource(self):
        res = config.get_resource('example/get_thing,abc')
        self.assertDictEqual(res.to_dict(), {'id': 'abc'})

    def test_get_tag(self):
        res = config.example_list.get_tag('test')
        self.assertDictEqual(res.to_dict(), {'id': 'test'})
