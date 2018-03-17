import os
import yaml
from six import StringIO
from pyauto.core import taskgen
from pyauto.util import yamlutil
from unittest import TestCase
from collections import OrderedDict


example_targets = {
    'deployments': {
        'name': 'dep',
        'list': ['east', 'west'],
    },
    'apps': {
        'name': 'app',
        'depends': 'deployments',
        'list': ['web', 'api']
    },
    'services': {
        'name': ['app', 'srv'],
        'depends': 'deployments',
        'map': [{'web': ['redis']}, {'api': ['postgres']}]
    }
}


class Targets(TestCase):
    def test_init(self):
        taskgen.Targets(example_targets)

    def test_get_target(self):
        targets = taskgen.Targets(example_targets)
        target = targets.get_target('apps')
        self.assertIsInstance(target, taskgen.Target)
        target = targets.get_target('apps.only')
        self.assertIsInstance(target, taskgen.Target)


class Target(TestCase):
    def setUp(self):
        self.targets = taskgen.Targets(example_targets)

    def test_get_ancestry(self):
        target = self.targets.get_target('apps')
        ancestry = target.get_ancestry()
        self.assertEqual(len(ancestry), 2)
        self.assertEqual('dep', ancestry[0].name)
        self.assertEqual('app', ancestry[1].name)

    def test_get_ancestry_list_only(self):
        target = self.targets.get_target('apps.only')
        ancestry = target.get_ancestry()
        self.assertEqual(len(ancestry), 1)
        self.assertEqual('app', ancestry[0].name)

    def test_get_ancestry_map_only(self):
        target = self.targets.get_target('services.only')
        ancestry = target.get_ancestry()
        self.assertEqual(len(ancestry), 1)
        self.assertEqual(['app', 'srv'], ancestry[0].name)

    def test_get_contexts(self):
        target = self.targets.get_target('apps')
        contexts = target.get_contexts()
        expected = [
            {'dep': 'east', 'app': 'web'},
            {'dep': 'east', 'app': 'api'},
            {'dep': 'west', 'app': 'web'},
            {'dep': 'west', 'app': 'api'}]
        self.assertListEqual(expected, contexts)

    def test_get_contexts_map(self):
        target = self.targets.get_target('services')
        contexts = target.get_contexts()
        expected = [
            {'dep': 'east', 'app': 'web', 'srv': 'redis'},
            {'dep': 'east', 'app': 'api', 'srv': 'postgres'},
            {'dep': 'west', 'app': 'web', 'srv': 'redis'},
            {'dep': 'west', 'app': 'api', 'srv': 'postgres'}]
        self.assertListEqual(expected, contexts)

    def test_get_contexts_map_only(self):
        target = self.targets.get_target('services.only')
        contexts = target.get_contexts()
        expected = [
            {'app': 'web', 'srv': 'redis'},
            {'app': 'api', 'srv': 'postgres'}]
        self.assertListEqual(expected, contexts)


class Tasks(TestCase):
    def setUp(self):
        self.targets = taskgen.Targets(example_targets)

    def test_init(self):
        tasks = taskgen.Tasks({
            'logins': {
                'deployments': [
                    {'{{ dep }}_login': ['login,{{ dep }}']},
                    {'login': ['login,{{ dep }}']},
                ]
            }
        }, self.targets)
        templates = tasks.get_templates('logins')
        self.assertIsInstance(templates, taskgen.TaskTemplates)

    def test_render(self):
        tasks = taskgen.Tasks({
            'logins': OrderedDict([
                ('deployments', [
                    {'{{ dep }}_login': ['login,{{ dep }}']},
                    {'login': ['{{ dep }}_login']},
                ])
            ]),
            'deploy': OrderedDict([
                ('apps', [
                    {'{{ dep }}_{{ app }}_deploy': [
                        'deploy,{{ dep }}_{{ app }}']},
                    {'{{ dep }}_deploy': [
                        '{{ dep }}_{{ app }}_deploy']}
                ]),
                ('deployments', [
                    {'deploy': ['{{ dep }}_deploy']},
                ]),
                ('__plain__', [
                    {'deploy_all': ['logins', 'deploy']}
                ])
            ])
        }, self.targets)
        result = tasks.render()
        expected = OrderedDict([
            ('east_login', ['login,east']),
            ('west_login', ['login,west']),
            ('login', ['east_login', 'west_login']),
            ('east_web_deploy', ['deploy,east_web']),
            ('east_api_deploy', ['deploy,east_api']),
            ('west_web_deploy', ['deploy,west_web']),
            ('west_api_deploy', ['deploy,west_api']),
            ('east_deploy', ['east_web_deploy', 'east_api_deploy']),
            ('west_deploy', ['west_web_deploy', 'west_api_deploy']),
            ('deploy', ['east_deploy', 'west_deploy']),
            ('deploy_all', ['logins', 'deploy'])])
        self.assertDictEqual(result, expected)


class TaskTemplates(TestCase):
    def setUp(self):
        self.targets = taskgen.Targets({
            'deployments': {
                'name': 'dep',
                'list': ['east', 'west'],
            }
        })

    def test_init(self):
        tt = taskgen.TaskTemplates({
            'deployments': [
                {'{{ dep }}_login': ['login,{{ dep }}']},
                {'login': ['login,{{ dep }}']},
            ]
        }, self.targets)

    def test_render(self):
        tt = taskgen.TaskTemplates({
            'deployments': [
                {'{{ dep }}_login': ['login,{{ dep }}']},
                {'login': ['login,{{ dep }}']},
            ]
        }, self.targets)
        result = tt.render()
        expected = OrderedDict([
            ('east_login', ['login,east']),
            ('west_login', ['login,west']),
            ('login', ['login,east', 'login,west'])])
        self.assertDictEqual(result, expected)


class TaskTemplate(TestCase):
    def test_init(self):
        taskgen.TaskTemplate([
            {'{{ dep }}_login': ['login,{{ dep }}']},
            {'logint': ['login,{{ dep }}']},
        ], [{'dep': 'east'}, {'dep': 'west'}])

    def test_render(self):
        tt = taskgen.TaskTemplate([
            {'{{ dep }}_login': ['login,{{ dep }}']},
            {'login': ['login,{{ dep }}']},
        ], [{'dep': 'east'}, {'dep': 'west'}])
        result = tt.render()
        expected = OrderedDict([
            ('east_login', ['login,east']),
            ('west_login', ['login,west']),
            ('login', ['login,east', 'login,west'])
        ])
        self.assertDictEqual(result, expected)


class TaskTemplateEntry(TestCase):
    def test_init(self):
        taskgen.TaskTemplateEntry(
            {'{{ dep }}_login': ['login,{{ dep }}']}, [{'dep': 'east'}])

    def test_render(self):
        tte = taskgen.TaskTemplateEntry(
            {'{{ dep }}_login': ['login,{{ dep }}']}, [{'dep': 'east'}])
        result = tte.render()
        expected = OrderedDict([('east_login', ['login,east'])])
        self.assertEqual(result, expected)


class ListTemplate(TestCase):
    def setUp(self):
        self.list_templates = ['{{ col1 }}_{{ col2 }}_foo']

    def test_init(self):
        taskgen.ListTemplate(self.list_templates)

    def test_render(self):
        lt = taskgen.ListTemplate(self.list_templates)
        self.assertListEqual(lt.render(col1='a', col2='b'), ['a_b_foo'])
