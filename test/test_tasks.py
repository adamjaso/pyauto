import os
from collections import OrderedDict
from unittest import TestCase
import test.example.commands as example_commands
import test.example.config as example_config
from pyauto import tasks as pyauto_tasks, config as pyauto_config


test_example_commands = 'test.example.commands'
test_example_func_name = 'do_thing'
task_seq_name = 'do_things'
config_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'example/config.example.yml')
with open(config_file) as f:
    config_str = f.read().strip()
config = pyauto_config.load(config_file)


def get_thing(id):
    return OrderedDict([
        ('id', id)
    ])


def get_things():
    return [get_thing(task_id) for task_id in ['jkl', 'mno']]


def get_do_thing(id):
    return ','.join(['do_thing', id])


def get_do_things():
    return [get_do_thing(task_id) for task_id in ['jkl', 'mno']]


def get_task_sequence(seq_name, task_ids):
    return (seq_name, [get_do_thing(task_id) for task_id in task_ids])


def get_task_modules():
    return [
        test_example_commands,
    ]


def get_config_dict():
    return OrderedDict([
        ('example', OrderedDict([('things', get_things())])),
    ])


def get_config():
    return pyauto_config.Config(get_config_dict())


def get_task_dict():
    return OrderedDict([(task_seq_name, get_do_things())])


class TestTaskSequences(TestCase):
    def test_init(self):
        pyauto_tasks.TaskSequences(
                get_task_modules(),
                get_task_dict(),
                get_config())

    def test_get_task(self):
        tasks = pyauto_tasks.TaskSequences(
                get_task_modules(),
                get_task_dict(),
                get_config())
        mod, fun = tasks.get_task(test_example_func_name)
        self.assertEqual(mod, example_commands)
        self.assertEqual(fun.__name__, test_example_func_name)

    def test_get_task_sequence(self):
        tasks = pyauto_tasks.TaskSequences(
                get_task_modules(),
                get_task_dict(),
                get_config())
        task_seq = tasks.get_task_sequence(task_seq_name)
        self.assertIsInstance(task_seq, pyauto_tasks.TaskSequence)
        self.assertEqual(task_seq.task_name, task_seq_name)


class TestTaskSequence(TestCase):
    def test_task_sig(self):
        tasks = pyauto_tasks.TaskSequences(
                get_task_modules(),
                get_task_dict(),
                get_config())
        task_seq = tasks.get_task_sequence(task_seq_name)
        self.assertEqual(task_seq.task_sig,
                         task_seq_name + ' (  )')

    def test_get_tasks(self):
        tasks = pyauto_tasks.TaskSequences(
                get_task_modules(),
                get_task_dict(),
                get_config())
        task_seq = tasks.get_task_sequence(task_seq_name)
        tasks1 = task_seq.get_tasks()
        tasks2 = get_do_things()
        for i in range(len(tasks1)):
            self.assertIsInstance(tasks1[i], pyauto_tasks.Task)
            self.assertEqual(tasks1[i].orig, tasks2[i])

    def test_to_tree(self):
        tasks = pyauto_tasks.TaskSequences(
                get_task_modules(),
                get_task_dict(),
                get_config())
        task_seq = tasks.get_task_sequence(task_seq_name)
        tree1 = task_seq.to_tree()
        tree2 = OrderedDict([(task_seq_name, [
            pyauto_tasks.Task(tasks, ts).to_tree()
            for ts in get_do_things()])])
        self.assertDictEqual(tree1, tree2)


class TestTask(TestCase):
    def test_module_func_name(self):
        tasks = pyauto_tasks.TaskSequences(
                get_task_modules(),
                get_task_dict(),
                get_config())
        task = pyauto_tasks.Task(tasks, 'do_thing,abc')
        self.assertEqual(task.module_func_name,
                         'test.example.commands.do_thing')

    def test_module_func_args(self):
        tasks = pyauto_tasks.TaskSequences(
                get_task_modules(),
                get_task_dict(),
                get_config())
        task = pyauto_tasks.Task(tasks, 'do_thing,abc')
        self.assertEqual(task.module_func_args,
                         'test.example.commands.do_thing ( abc )')

    def test_invoke(self):
        config_dict = get_config_dict()
        config_dict['tasks'] = get_task_dict()
        config = pyauto_config.Config(config_dict)

        tasks = pyauto_tasks.TaskSequences(
                get_task_modules(),
                get_task_dict(),
                config)
        task = pyauto_tasks.Task(tasks, 'do_thing,jkl')
        res = task.invoke()
        self.assertDictEqual(res.to_dict(), OrderedDict([('id', 'jkl')]))
