import json
from pyauto.util import yamlutil
from pyauto.core import api, taskapi
from unittest import TestCase
from collections import OrderedDict
from . import data


def get_task_sequences():
    return taskapi.TaskSequences(data.sequences)


def get_repository():
    r = api.Repository()
    r.load_packages(data.packages)
    r.load_objects(data.objects)
    return r


class General(TestCase):
    def test_parse_task(self):
        res = taskapi.parse_task(
            'file.File.render_template abc1')
        self.assertEqual(res[0], 'file.File.render_template')
        self.assertEqual(res[1], 'abc1')
        res = taskapi.parse_task(
            'file.File.render_template abc1 "{a: 1, b: 2}"')
        self.assertEqual(res[0], 'file.File.render_template')
        self.assertEqual(res[1], 'abc1')
        self.assertDictEqual(res[2], {'a': 1, 'b': 2})


class TaskSequenceArguments(TestCase):
    def setUp(self):
        self.args = taskapi.TaskSequenceArguments('app', {
            'app': 'deploy.App', 'reg': 'deploy.Region'})

    def test_is_compatible(self):
        args2 = taskapi.TaskSequenceArguments('app', {
            'app': 'deploy.App'})
        self.args.is_compatible(args2.kinds)

    def test_has_variable(self):
        self.assertTrue(self.args.has_variable('app'))
        self.assertFalse(self.args.has_variable('app2'))

    def test_assert_variable(self):
        self.args.assert_variable('app')
        with self.assertRaises(taskapi.InvalidTaskSequence):
            self.args.assert_variable('app2')

    def test_build_context(self):
        result = self.args.build_context({'deploy.App': ['a', 'b'],
                                          'deploy.Region': ['c', 'd']})
        self.assertListEqual([p for p in result], [
            {'app': 'a', 'reg': 'c'},
            {'app': 'a', 'reg': 'd'},
            {'app': 'b', 'reg': 'c'},
            {'app': 'b', 'reg': 'd'}])


class TaskSequenceQuery(TestCase):
    def setUp(self):
        self.sequences = get_task_sequences()
        self.sequence = self.sequences.get_sequence('deploy_app')
        self.query = taskapi.TaskSequenceQuery(self.sequence, data.query)

    def test_get_variable(self):
        res = self.query.get_variable('app')
        self.assertDictEqual(res, OrderedDict([('tags', ['a', 'b', 'c'])]))


class TaskSequences(TestCase):
    def setUp(self):
        self.repository = get_repository()
        self.sequences = get_task_sequences()
        self.query_results = data.query

    def test_validate_sequences(self):
        self.sequences.validate_sequences()

    def test_get_argument(self):
        args = self.sequences.get_argument('application')
        self.assertEqual(args.name, 'application')
        self.assertIsInstance(args, taskapi.TaskSequenceArguments)

    def test_get_sequence(self):
        seq = self.sequences.get_sequence('deploy_app')
        self.assertEqual(seq.name, 'deploy_app')
        self.assertIsInstance(seq, taskapi.TaskSequence)

    def test_resolve_context(self):
        res = self.sequences.resolve_context(
            self.repository, self.query_results, 'deploy_app')
        res = [{k: v.ref for k, v in pair.items()} for pair in res]
        self.assertListEqual(res, [
            {'reg': 'deploy.Region/abc1', 'app': 'deploy.App/a'},
            {'reg': 'deploy.Region/abc1', 'app': 'deploy.App/b'},
            {'reg': 'deploy.Region/abc1', 'app': 'deploy.App/c'},
            {'reg': 'deploy.Region/abc2', 'app': 'deploy.App/a'},
            {'reg': 'deploy.Region/abc2', 'app': 'deploy.App/b'},
            {'reg': 'deploy.Region/abc2', 'app': 'deploy.App/c'},
            {'reg': 'deploy.Region/abc3', 'app': 'deploy.App/a'},
            {'reg': 'deploy.Region/abc3', 'app': 'deploy.App/b'},
            {'reg': 'deploy.Region/abc3', 'app': 'deploy.App/c'},])

    def test_resolve(self):
        res = self.sequences.resolve(
            self.repository, self.query_results, 'deploy_app')
        self.assertListEqual(res, [
            'deploy.Region.login abc1',
            'deploy.Region.login abc2',
            'deploy.Region.login abc3',
            'file.Directory.rmtree abc1_a',
            'file.Directory.rmtree abc1_b',
            'file.Directory.rmtree abc1_c',
            'file.Directory.rmtree abc2_a',
            'file.Directory.rmtree abc2_b',
            'file.Directory.rmtree abc2_c',
            'file.Directory.rmtree abc3_a',
            'file.Directory.rmtree abc3_b',
            'file.Directory.rmtree abc3_c',
            'file.Directory.copytree abc1_a',
            'file.Directory.copytree abc1_b',
            'file.Directory.copytree abc1_c',
            'file.Directory.copytree abc2_a',
            'file.Directory.copytree abc2_b',
            'file.Directory.copytree abc2_c',
            'file.Directory.copytree abc3_a',
            'file.Directory.copytree abc3_b',
            'file.Directory.copytree abc3_c',
            'file.File.render_template abc1_a',
            'file.File.render_template abc1_b',
            'file.File.render_template abc1_c',
            'file.File.render_template abc2_a',
            'file.File.render_template abc2_b',
            'file.File.render_template abc2_c',
            'file.File.render_template abc3_a',
            'file.File.render_template abc3_b',
            'file.File.render_template abc3_c',
            'deploy.RegionApp.push_app abc1_a',
            'deploy.RegionApp.push_app abc1_b',
            'deploy.RegionApp.push_app abc1_c',
            'deploy.RegionApp.push_app abc2_a',
            'deploy.RegionApp.push_app abc2_b',
            'deploy.RegionApp.push_app abc2_c',
            'deploy.RegionApp.push_app abc3_a',
            'deploy.RegionApp.push_app abc3_b',
            'deploy.RegionApp.push_app abc3_c'])

    def test_run_sequence(self):
        query = {
            'app': {'tags': ['a', 'b'],
            'reg': {'tags': ['abc']}}}
        res = self.sequences.run_sequence(
            self.repository, query, 'deploy_app')
        self.assertListEqual([i['task'] for i in res], [
            'deploy.Region.login',
            'deploy.Region.login',
            'deploy.Region.login',
            'file.Directory.rmtree',
            'file.Directory.rmtree',
            'file.Directory.rmtree',
            'file.Directory.rmtree',
            'file.Directory.rmtree',
            'file.Directory.rmtree',
            'file.Directory.copytree',
            'file.Directory.copytree',
            'file.Directory.copytree',
            'file.Directory.copytree',
            'file.Directory.copytree',
            'file.Directory.copytree',
            'file.File.render_template',
            'file.File.render_template',
            'file.File.render_template',
            'file.File.render_template',
            'file.File.render_template',
            'file.File.render_template',
            'deploy.RegionApp.push_app',
            'deploy.RegionApp.push_app',
            'deploy.RegionApp.push_app',
            'deploy.RegionApp.push_app',
            'deploy.RegionApp.push_app',
            'deploy.RegionApp.push_app'])


class TaskSequence(TestCase):
    def setUp(self):
        self.repository = get_repository()
        self.sequences = get_task_sequences()
        self.sequence = self.sequences.get_sequence('deploy_app')
        self.query = taskapi.TaskSequenceQuery(self.sequence, data.query)
        self.query_results = self.repository.query(
            self.query.query_args, resolve=True)

    def test_validate(self):
        self.sequence.validate()

    def test_resolve_context(self):
        res = self.sequence.resolve_context(self.query_results)
        res = [{k: v.ref for k, v in pair.items()} for pair in res]
        self.assertListEqual(res, [
            {'reg': 'deploy.Region/abc1', 'app': 'deploy.App/a'},
            {'reg': 'deploy.Region/abc1', 'app': 'deploy.App/b'},
            {'reg': 'deploy.Region/abc1', 'app': 'deploy.App/c'},
            {'reg': 'deploy.Region/abc2', 'app': 'deploy.App/a'},
            {'reg': 'deploy.Region/abc2', 'app': 'deploy.App/b'},
            {'reg': 'deploy.Region/abc2', 'app': 'deploy.App/c'},
            {'reg': 'deploy.Region/abc3', 'app': 'deploy.App/a'},
            {'reg': 'deploy.Region/abc3', 'app': 'deploy.App/b'},
            {'reg': 'deploy.Region/abc3', 'app': 'deploy.App/c'},])

    def test_resolve(self):
        res = []
        self.sequence.resolve(self.query_results, res)
        self.assertListEqual(res, [
            'deploy.Region.login abc1',
            'deploy.Region.login abc2',
            'deploy.Region.login abc3',
            'file.Directory.rmtree abc1_a',
            'file.Directory.rmtree abc1_b',
            'file.Directory.rmtree abc1_c',
            'file.Directory.rmtree abc2_a',
            'file.Directory.rmtree abc2_b',
            'file.Directory.rmtree abc2_c',
            'file.Directory.rmtree abc3_a',
            'file.Directory.rmtree abc3_b',
            'file.Directory.rmtree abc3_c',
            'file.Directory.copytree abc1_a',
            'file.Directory.copytree abc1_b',
            'file.Directory.copytree abc1_c',
            'file.Directory.copytree abc2_a',
            'file.Directory.copytree abc2_b',
            'file.Directory.copytree abc2_c',
            'file.Directory.copytree abc3_a',
            'file.Directory.copytree abc3_b',
            'file.Directory.copytree abc3_c',
            'file.File.render_template abc1_a',
            'file.File.render_template abc1_b',
            'file.File.render_template abc1_c',
            'file.File.render_template abc2_a',
            'file.File.render_template abc2_b',
            'file.File.render_template abc2_c',
            'file.File.render_template abc3_a',
            'file.File.render_template abc3_b',
            'file.File.render_template abc3_c',
            'deploy.RegionApp.push_app abc1_a',
            'deploy.RegionApp.push_app abc1_b',
            'deploy.RegionApp.push_app abc1_c',
            'deploy.RegionApp.push_app abc2_a',
            'deploy.RegionApp.push_app abc2_b',
            'deploy.RegionApp.push_app abc2_c',
            'deploy.RegionApp.push_app abc3_a',
            'deploy.RegionApp.push_app abc3_b',
            'deploy.RegionApp.push_app abc3_c'])


class SubTaskSequence(TestCase):
    def setUp(self):
        self.sequences = get_task_sequences()
        self.sequence = self.sequences.get_sequence('region_login')
        self.subtask = self.sequence.sequence[0]

    def test_render(self):
        res = self.subtask.render(reg={'tag': 'abc1'})
        self.assertEqual(res, 'deploy.Region.login abc1')
