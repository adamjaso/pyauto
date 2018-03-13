import six
import itertools
from jinja2 import Environment
from collections import OrderedDict


class TaskTemplatesList(object):
    def __init__(self, tasks, main_context):
        self.tasks = [
            TaskTemplates(task, main_context)
            for task in tasks
        ]

    def render(self):
        tasks = OrderedDict()
        for task in self.tasks:
            exported = task.render()
            for k in exported:
                if k in tasks:
                    raise Exception('duplicate task key found: {0}'.format(k))
            tasks.update(exported)
        return tasks


class TaskTemplates(object):
    def __init__(self, config, main_context):
        self.list_templates = {
            key: ListTemplate(task_list)
            for key, task_list in config.get('list_templates', {}).items()
        }
        self.task_templates = [
            TaskTemplate(task_template, self, main_context)
            for task_template in config.get('task_templates', [])
        ]

    def render(self):
        tasks = OrderedDict()
        for task in self.task_templates:
            exported = task.render()
            for k in exported:
                if k in tasks:
                    raise Exception('duplicate task key found: {0}'.format(k))
            tasks.update(exported)
        return tasks


class ListTemplate(object):
    def __init__(self, task_list):
        env = Environment()
        self.task_list = [
            env.from_string(task_template).render
            for task_template in task_list
        ]

    def render(self, **context):
        return [str(render(**context)) for render in self.task_list]


class TaskTemplate(object):
    def __init__(self, config, parent, main_context):
        self.config = parent
        self.columns = config.get('columns', [])
        self.contexts = [
            Contexts(self.columns, contexts, main_context)
            for contexts in config.get('contexts', [])
        ]
        self.task_templates = [
            TaskTemplateEntry(
                template, self)
            for template in config.get('task_templates', [])
        ]

    def render(self):
        tasks = OrderedDict()
        for task in self.task_templates:
            exported = task.render()
            for k in exported:
                if k in tasks:
                    raise Exception('duplicate task key found: {0}'.format(k))
            tasks.update(exported)
        return tasks


class TaskTemplateEntry(object):
    def __init__(self, config, task_template):
        self.config = task_template
        if 'name' in config:
            self.name = config['name']
            self.subtasks = config['subtasks']
        else:
            self.name = next(iter(config.keys()))
            self.subtasks = config[self.name]

        env = Environment()
        self.render_name = env.from_string(self.name).render
        if isinstance(self.subtasks, six.string_types):
            self.subtasks = self.config.config.list_templates[self.subtasks]
        else:
            self.subtasks = ListTemplate(self.subtasks)

    def render(self):
        tasks = OrderedDict()
        for contexts in self.config.contexts:
            for context in contexts:
                name = str(self.render_name(**context))
                if name not in tasks:
                    tasks[name] = []
                subtasks = self.subtasks.render(**context)
                tasks[name].extend(subtasks)
        return tasks


class Contexts(object):
    def __init__(self, columns, foreach, main_context):
        self.items = []
        for key in foreach:
            if not isinstance(key, six.string_types) and isinstance(key, list):
                self.items.append(key)
            elif key not in main_context:
                raise Exception('"{0}" key not found'.format(key))
            else:
                self.items.append(main_context[key])
        self.product = [list(row) for row in itertools.product(*self.items)]
        self.contexts = [dict(zip(columns, row)) for row in self.product]

    def __iter__(self):
        return iter(self.contexts)

    def __len__(self):
        return len(self.contexts)


def generate_tasks(tasks, **context):
    return TaskTemplatesList(tasks, context).render()


def main():
    import os
    import json
    import argparse
    from pyauto.util import yamlutil
    args = argparse.ArgumentParser()
    args.add_argument('-f', dest='filename', required=True)
    args.add_argument('-k', '--key', dest='key', required=True)
    args.add_argument('--render', dest='render', action='store_true')
    args.add_argument('--to-yaml', dest='to_yaml', action='store_true')
    args = args.parse_args()

    with open(os.path.abspath(args.filename)) as f:
        config = yamlutil.load_dict(f.read())

    tasks = TaskTemplatesList(config[args.key], config)
    if not args.render:
        print(json.dumps(config, indent=2))
        return

    rendered = tasks.render()
    if args.to_yaml:
        print(yamlutil.dump_dict(rendered))
    else:
        print(json.dumps(rendered, indent=2))


if '__main__' == __name__:
    main()
