import os
import sys
import inspect
from pyauto.core import doctool
from unittest import TestCase
from subprocess import Popen
from collections import OrderedDict

dirname = os.path.dirname(os.path.abspath(__file__))
example_package = os.path.join(dirname, 'doctool-example')
sys.path.insert(0, example_package)

import doctool_example
from doctool_example import config as doctool_config
from doctool_example import commands as doctool_commands


class Member(TestCase):
    def setUp(self):
        self.cmdmem = doctool.Member(doctool_commands, 'get_thing')
        self.confmem = doctool.Member(doctool_commands, 'make_thing')
        self.thingmem = doctool.Member(doctool_config, 'Thing')

    def test_init(self):
        self.assertTrue(inspect.isfunction(self.cmdmem.member))

    def test_name(self):
        self.assertEqual(self.cmdmem.name, 'doctool_example.commands.get_thing')

    def test_is_command_func(self):
        self.assertTrue(self.cmdmem.is_command_func())

    def test_is_helper_function(self):
        self.assertTrue(self.confmem.is_helper_function())

    def test_is_config_class(self):
        self.assertTrue(self.thingmem.is_config_class())

    def test_get_class_methods(self):
        methods = self.thingmem.get_class_methods()
        self.assertListEqual(methods, [
            OrderedDict([
                ('name', 'do_thing'),
                ('class', 'doctool_example.config.Thing'),
                ('module', 'doctool_example.config'),
                ('kind', 'classmethod'),
                ('resource', True),
                ('argstring', '(tag)'),
                ('description', 'Does a thing')]),
            OrderedDict([
                ('name', 'get_thing'),
                ('class', 'doctool_example.config.Thing'),
                ('module', 'doctool_example.config'),
                ('kind', 'classmethod'),
                ('resource', True),
                ('argstring', '(tag)'),
                ('description', 'Gets a thing')])
        ])

    def test_class_attributes(self):
        attrs = self.thingmem.get_class_attributes()
        for name, func in attrs.items():
            self.assertEqual(name, func.__name__)
            self.assertTrue(hasattr(self.thingmem.member, name))
            self.assertTrue(inspect.isfunction(func))


class Module(TestCase):
    expected_pkg_commands = OrderedDict([
        ('name', 'doctool_example.commands'),
        ('module', 'doctool_example.commands'),
        ('description', None),
        ('members', [
            OrderedDict([
                ('name', 'do_thing'),
                ('fullname', 'doctool_example.commands.do_thing'),
                ('module', 'doctool_example.commands'),
                ('kind', 'command'),
                ('fullargstring', '(config)'),
                ('argstring', '()'),
                ('description', 'Does something')]),
            OrderedDict([
                ('name', 'get_thing'),
                ('fullname', 'doctool_example.commands.get_thing'),
                ('module', 'doctool_example.commands'),
                ('kind', 'command'),
                ('fullargstring', '(config)'),
                ('argstring', '()'),
                ('description', 'Gets something')]),
            OrderedDict([
                ('name', 'make_thing'),
                ('fullname', 'doctool_example.commands.make_thing'),
                ('module', 'doctool_example.commands'),
                ('kind', 'helperfunction'),
                ('argstring', '(config_)'),
                ('description', 'Make a something')])
        ])
    ])

    expected_mod_config = OrderedDict([
        ('name', 'doctool_example.config'),
        ('module', 'doctool_example.config'),
        ('description', None),
        ('members', [
            OrderedDict([
                ('name', 'Thing'),
                ('fullname', 'doctool_example.config.Thing'),
                ('module', 'doctool_example.config'),
                ('kind', 'config'),
                ('config_key', 'things'),
                ('description', 'A representation of a thing'),
                ('classmethods', [
                    OrderedDict([
                        ('name', 'do_thing'), 
                        ('class', 'doctool_example.config.Thing'),
                        ('module', 'doctool_example.config'),
                        ('kind', 'classmethod'),
                        ('resource', True),
                        ('argstring', '(tag)'),
                        ('description', 'Does a thing')]),
                    OrderedDict([
                        ('name', 'get_thing'),
                        ('class', 'doctool_example.config.Thing'),
                        ('module', 'doctool_example.config'),
                        ('kind', 'classmethod'),
                        ('resource', True),
                        ('argstring', '(tag)'),
                        ('description', 'Gets a thing')])
                ])
            ])
        ])
    ])

    def setUp(self):
        self.pkg = doctool.Module('doctool_example')
        self.mod = doctool.Module('doctool_example.config')

    def test_list_modules(self):
        self.assertEqual(len(list(self.pkg.list_modules())), 2)

    def test_get_commands(self):
        modules = list(self.pkg.list_modules())
        commands = self.pkg.get_commands(next(
            m for m in modules if m.__name__.endswith('commands')))
        self.assertDictEqual(commands, self.expected_pkg_commands)

    def test_extract_commands(self):
        cmds = self.pkg.extract_commands()
        self.assertDictEqual(cmds, OrderedDict([
            ('doctool_example.commands', self.expected_pkg_commands),
            ('doctool_example.config', self.expected_mod_config)
        ]))
        cmds = self.mod.extract_commands()
        self.assertDictEqual(cmds, OrderedDict([
            ('doctool_example.config', self.expected_mod_config)
        ]))


class Functions(TestCase):
    test_results = OrderedDict([
        ('doctool_example', OrderedDict([
            ('id', 'doctool_example'),
            ('name', 'doctool_example'),
            ('description', None),
            ('modules', [
                OrderedDict([
                    ('id', 'doctool_example.commands'),
                    ('package', 'doctool_example'),
                    ('description', None)]),
                OrderedDict([
                    ('id', 'doctool_example.config'),
                    ('package', 'doctool_example'),
                    ('description', None)])]),
                    ('commands', [
                        OrderedDict([
                            ('id', 'doctool_example.commands.do_thing'),
                            ('name', 'do_thing'),
                            ('module', 'doctool_example.commands'),
                            ('kind', 'command'),
                            ('fullargstring', '(config)'),
                            ('argstring', '()'),
                            ('description', 'Does something')]),
                        OrderedDict([
                            ('id', 'doctool_example.commands.get_thing'),
                            ('name', 'get_thing'),
                            ('module', 'doctool_example.commands'),
                            ('kind', 'command'),
                            ('fullargstring', '(config)'),
                            ('argstring', '()'),
                            ('description', 'Gets something')])
                    ]),
                    ('helperfunctions', [
                        OrderedDict([
                            ('id', 'doctool_example.commands.make_thing'),
                            ('name', 'make_thing'),
                            ('module', 'doctool_example.commands'),
                            ('kind', 'helperfunction'),
                            ('argstring', '(config_)'),
                            ('description', 'Make a something')])
                    ]),
                    ('resources', [
                        OrderedDict([
                            ('id', 'doctool_example.config.Thing.do_thing'),
                            ('config', 'doctool_example.config.Thing'),
                            ('config_key', 'things'),
                            ('name', 'do_thing'),
                            ('kind', 'resource'),
                            ('resource', True),
                            ('argstring', '(tag)'),
                            ('description', 'Does a thing')]),
                        OrderedDict([
                            ('id', 'doctool_example.config.Thing.get_thing'),
                            ('config', 'doctool_example.config.Thing'),
                            ('config_key', 'things'),
                            ('name', 'get_thing'),
                            ('kind', 'resource'),
                            ('resource', True),
                            ('argstring', '(tag)'),
                            ('description', 'Gets a thing')])
                    ]),
                    ('configs', [
                        OrderedDict([
                            ('id', 'doctool_example.config.Thing'),
                            ('name', 'Thing'),
                            ('module', 'doctool_example.config'),
                            ('kind', 'config'),
                            ('config_key', 'things'),
                            ('description','A representation of a thing'),
                            ('properties', []),
                            ('methods', [
                                OrderedDict([
                                    ('name', 'do_thing'),
                                    ('kind', 'configmethod'),
                                    ('resource', True),
                                    ('argstring', '(tag)'),
                                    ('description', 'Does a thing')]),
                                OrderedDict([
                                    ('name', 'get_thing'),
                                    ('kind', 'configmethod'),
                                    ('resource', True),
                                    ('argstring', '(tag)'),
                                    ('description', 'Gets a thing')])
                            ])
                        ])
                    ]),
                    ('missing_descriptions', [
                        'doctool_example',
                        'doctool_example.commands',
                        'doctool_example',
                        'doctool_example.config'
                    ])
                ]))
            ])

    def test_aggregate_results(self):
        mod = doctool.Module('doctool_example')
        cmds = mod.extract_commands()
        results = doctool.aggregate_results(cmds, None)
        self.assertDictEqual(results, self.test_results)
