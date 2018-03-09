import os
import yaml
from six import StringIO
from pyauto.core import taskgen
from pyauto.util import yamlutil
from unittest import TestCase

example_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'taskgen-example')
values_file = os.path.join(example_dir, 'values.yml')
result_file = os.path.join(example_dir, 'result.yml')
tasks_file = os.path.join(example_dir, 'tasks.yml')


expected_contexts = [
    {'app': 'a1', 'dep': 'd1'}, {'app': 'a2', 'dep': 'd1'},
    {'app': 'a1', 'dep': 'd2'}, {'app': 'a2', 'dep': 'd2'},
]


def get_values():
    with open(values_file) as f:
        return yamlutil.load_dict(f.read())


def get_expected_result():
    with open(result_file) as f:
        return yamlutil.load_dict(f.read())


def get_tasks():
    with open(tasks_file) as f:
        return yamlutil.load_dict(f.read())['all_apps_in_all_regions']


class TaskGenerator(TestCase):
    def setUp(self):
        self.tasks = get_tasks()
        self.values = get_values()
        self.gen = taskgen.TaskGenerator(self.tasks, self.values)

    def test_init(self):
        tg = self.gen
        for ttl in tg.list_templates.values():
            self.assertIsInstance(ttl, taskgen.TaskTemplateList)
        for tt in tg.task_templates:
            self.assertIsInstance(tt, taskgen.TaskTemplate)
        for item in tg.foreach_items:
            self.assertIsInstance(item, list)
        self.assertListEqual(tg.foreach_product, [['d1', 'a1'], ['d1', 'a2'],
                                                  ['d2', 'a1'], ['d2', 'a2']])
        self.assertListEqual(tg.foreach_contexts, expected_contexts)
        self.assertListEqual(tg.columns, self.tasks['columns'])

    def test_get_foreach_context(self):
        deps = self.gen.get_foreach_context('dep')
        self.assertListEqual(deps, [{'dep': 'd1'}, {'dep': 'd2'}])
        apps = self.gen.get_foreach_context('app')
        self.assertListEqual(apps, [{'app': 'a1'}, {'app': 'a2'}])
        all_contexts = self.gen.get_foreach_context()
        self.assertListEqual(all_contexts, expected_contexts)

    def test_render(self):
        rendered = self.gen.render()
        result = get_expected_result()
        self.assertDictEqual(rendered, result['tasks'])
