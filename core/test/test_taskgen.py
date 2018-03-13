import os
import yaml
from six import StringIO
from pyauto.core import taskgen
from pyauto.util import yamlutil
from unittest import TestCase
from collections import OrderedDict


example_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'taskgen-example')
values_file = os.path.join(example_dir, 'values.yml')
result_file = os.path.join(example_dir, 'result.yml')
tasks_file = os.path.join(example_dir, 'tasks.yml')
expected_contexts = [{'col2': '1', 'col1': 'a'},
                     {'col2': '2', 'col1': 'a'},
                     {'col2': '1', 'col1': 'b'},
                     {'col2': '2', 'col1': 'b'}]
example_task_template_entry = {
    'dict': {
        'name': '{{ col1 }}_{{ col2 }}_foo',
        'subtasks': [
            '{{ col1 }}_{{ col2 }}_qux',
            '{{ col1 }}_{{ col2 }}_baz',
        ],
    },
    'string': {
        '{{ col1 }}_{{ col2 }}_foo': [
            '{{ col1 }}_{{ col2 }}_qux',
            '{{ col1 }}_{{ col2 }}_baz',
        ]
    },
    'reference': {
        '{{ col1 }}_{{ col2 }}_foo': 'col1_col2_foo'
    }
}
example_list_templates = {
    'col1_col2_foo': ['{{ col1 }}_{{ col2 }}_foo']
}
example_resource = {'list1': ['a', 'b'], 'list2': ['1', '2']}
expected_ttl_result = OrderedDict([
    ('d1_a1_clone', ['clone,d1_a1']),
    ('d1_a2_clone', ['clone,d1_a2']),
    ('d2_a1_clone', ['clone,d2_a1']),
    ('d2_a2_clone', ['clone,d2_a2']),
    ('d1_deploy', ['init_deployment,d1', 'd1_clone', 'd1_generate']),
    ('d2_deploy', ['init_deployment,d2', 'd2_clone', 'd2_generate']),
    ('d1_a1_s1_create', ['create_service,d1_a1_s1']),
    ('d1_a1_s2_create', ['create_service,d1_a1_s2']),
    ('d2_a1_s1_create', ['create_service,d2_a1_s1']),
    ('d2_a1_s2_create', ['create_service,d2_a1_s2']),
    ('d1_a2_s3_create', ['create_service,d1_a2_s3']),
    ('d2_a2_s3_create', ['create_service,d2_a2_s3']),
    ('d1_a1_create_services', ['d1_a1_s1_create', 'd1_a1_s2_create']),
    ('d2_a1_create_services', ['d2_a1_s1_create', 'd2_a1_s2_create']),
    ('d1_a2_create_services', ['d1_a2_s3_create']),
    ('d2_a2_create_services', ['d2_a2_s3_create'])])
expected_tts_result = OrderedDict([
    ('d1_a1_clone', ['clone,d1_a1']),
    ('d1_a2_clone', ['clone,d1_a2']),
    ('d2_a1_clone', ['clone,d2_a1']),
    ('d2_a2_clone', ['clone,d2_a2']),
    ('d1_deploy', ['init_deployment,d1', 'd1_clone', 'd1_generate']),
    ('d2_deploy', ['init_deployment,d2', 'd2_clone', 'd2_generate']),
    ('d1_a1_s1_create', ['create_service,d1_a1_s1']),
    ('d1_a1_s2_create', ['create_service,d1_a1_s2']),
    ('d2_a1_s1_create', ['create_service,d2_a1_s1']),
    ('d2_a1_s2_create', ['create_service,d2_a1_s2']),
    ('d1_a2_s3_create', ['create_service,d1_a2_s3']),
    ('d2_a2_s3_create', ['create_service,d2_a2_s3']),
    ('d1_a1_create_services', ['d1_a1_s1_create', 'd1_a1_s2_create']),
    ('d2_a1_create_services', ['d2_a1_s1_create', 'd2_a1_s2_create']),
    ('d1_a2_create_services', ['d1_a2_s3_create']),
    ('d2_a2_create_services', ['d2_a2_s3_create'])])
expected_tt_result = OrderedDict([
    ('d1_a1_clone', ['clone,d1_a1']),
    ('d1_a2_clone', ['clone,d1_a2']),
    ('d2_a1_clone', ['clone,d2_a1']),
    ('d2_a2_clone', ['clone,d2_a2'])])
expected_tte_result = OrderedDict([
    ('d1_a1_clone', ['clone,d1_a1']),
    ('d1_a2_clone', ['clone,d1_a2']),
    ('d2_a1_clone', ['clone,d2_a1']),
    ('d2_a2_clone', ['clone,d2_a2'])])


def get_values():
    with open(values_file) as f:
        return yamlutil.load_dict(f.read())


def get_expected_result():
    with open(result_file) as f:
        return yamlutil.load_dict(f.read())


def get_tasks():
    with open(tasks_file) as f:
        return yamlutil.load_dict(f.read())


class Contexts(TestCase):
    def test_init_simple(self):
        ctxs = taskgen.Contexts(['col1', 'col2'], [['a', 'b'], ['1', '2']], {})
        result = [ctx for ctx in ctxs]
        self.assertListEqual(expected_contexts, result)

    def test_init_complex(self):
        ctxs = taskgen.Contexts(['col1', 'col2'], ['list1', 'list2'],
                                example_resource)
        result = [ctx for ctx in ctxs]
        self.assertListEqual(expected_contexts, result)


class TaskTemplatesList(TestCase):
    def test_init(self):
        tasks = get_tasks()
        ttl = taskgen.TaskTemplatesList(tasks['tasks'], tasks)
        for tt in ttl.tasks:
            self.assertIsInstance(tt, taskgen.TaskTemplates)

    def test_render(self):
        tasks = get_tasks()
        ttl = taskgen.TaskTemplatesList(tasks['tasks'], tasks)
        result = ttl.render()
        self.assertDictEqual(result, expected_ttl_result)


class TaskTemplates(TestCase):
    def setUp(self):
        self.tasks = get_tasks()
        self.ttl = taskgen.TaskTemplatesList(self.tasks['tasks'], self.tasks)

    def test_init(self):
        tts = taskgen.TaskTemplates(self.tasks['tasks'][0], self.tasks)
        for lt in tts.list_templates.values():
            self.assertIsInstance(lt, taskgen.ListTemplate)
        for tt in tts.task_templates:
            self.assertIsInstance(tt, taskgen.TaskTemplate)

    def test_render(self):
        tts = taskgen.TaskTemplates(self.tasks['tasks'][0], self.tasks)
        result = tts.render()
        self.assertDictEqual(expected_tts_result, result)


class ListTemplate(TestCase):
    def test_init(self):
        task_list = next(iter(example_list_templates.values()))
        taskgen.ListTemplate(task_list)

    def test_render(self):
        task_list = next(iter(example_list_templates.values()))
        lt = taskgen.ListTemplate(task_list)
        self.assertListEqual(lt.render(col1='a', col2='b'), ['a_b_foo'])


class TaskTemplate(TestCase):
    def setUp(self):
        self.tasks = get_tasks()
        self.ttl = taskgen.TaskTemplatesList(self.tasks['tasks'], self.tasks)
        self.task = self.tasks['tasks'][0]['task_templates'][0]

    def test_init(self):
        taskgen.TaskTemplate(self.task, self.ttl.tasks[0], self.tasks)

    def test_render(self):
        self.tasks = get_tasks()
        self.ttl = taskgen.TaskTemplatesList(self.tasks['tasks'], self.tasks)
        task = self.tasks['tasks'][0]['task_templates'][0]
        tt = taskgen.TaskTemplate(self.task, self.ttl.tasks[0], self.tasks)
        result = tt.render()
        self.assertDictEqual(expected_tt_result, result)


class TaskTemplateEntry(TestCase):
    def setUp(self):
        self.tasks = get_tasks()
        self.ttl = taskgen.TaskTemplatesList(self.tasks['tasks'], self.tasks)
        self.task_template = \
            self.tasks['tasks'][0]['task_templates'][0]['task_templates'][0]
        self.tt = self.ttl.tasks[0].task_templates[0]
#        self.tt = taskgen.TaskTemplate(self.task_template, self.ttl.tasks[0], self.tasks)

    def test_init(self):
        taskgen.TaskTemplateEntry(
                self.task_template, self.tt)

    def test_render(self):
        tte = taskgen.TaskTemplateEntry(
            self.task_template, self.tt)
        result = tte.render()
        self.assertDictEqual(expected_tte_result, result)
