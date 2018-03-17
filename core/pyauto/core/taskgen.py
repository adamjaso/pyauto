import itertools
import six
from copy import copy
from jinja2 import Environment
from collections import OrderedDict
from pyauto.util import yamlutil


class Definitions(object):
    def __init__(self, config):
        self.targets = Targets(config['targets'])
        self.tasks = Tasks(config['tasks'], self.targets)


class Targets(object):
    def __init__(self, config):
        self.targets = OrderedDict()
        for name, target in config.items():
            self.targets[name] = Target(copy(target), self)
            only_target = copy(target)
            if 'depends' in only_target:
                del only_target['depends']
            self.targets[name + '.only'] = Target(only_target, self)

    def get_target(self, name):
        return self.targets[name]


class Target(object):
    def __init__(self, config, parent):
        self.config = parent
        self.name = config['name']
        self.depends = config.get('depends', None)
        self.map = config.get('map', None)
        self.list = config.get('list', None)

    def get_parent(self):
        return self.config.get_target(self.depends)

    def get_ancestry(self, result=None):
        if result is None:
            result = []
        result.insert(0, self)
        if self.depends:
            return self.get_parent().get_ancestry(result)
        else:
            return result

    def get_contexts(self):
        names = []
        ancestry = self.get_ancestry()
        product_lists = []
        for anc in ancestry:
            if isinstance(anc.name, list):
                names.extend(anc.name)
            else:
                names.append(anc.name)
            if anc.list:
                continue
            elif anc.map:
                list_ = []
                for i, item in enumerate(anc.map):
                    item_product = itertools.product(list(item.keys()),
                                                     list(item.values())[0])
                    item_product = [list(row) for row in item_product]
                    list_.extend(item_product)
                anc.list = list_

        rows_product = itertools.product(*[anc.list for anc in ancestry])
        rows = [list(row) for row in rows_product]
        for i, row in enumerate(rows):
            revised = []
            for cell in row:
                if isinstance(cell, list):
                    revised.extend(cell)
                else:
                    revised.append(cell)
            if len(names) != len(revised):
                raise Exception('name is misconfigured: {0} != {1}'
                                .format(len(names), len(revised)))
            rows[i] = dict(zip(names, revised))
        return rows


class Tasks(object):
    def __init__(self, config, targets):
        self.groups = OrderedDict([
            (group_id, TaskTemplates(val, targets))
            for group_id, val in config.items()
        ])

    def get_templates(self, name):
        return self.groups[name]

    def render(self):
        tasks = OrderedDict()
        for group_id, task in self.groups.items():
            exported = task.render()
            for k in exported:
                if k in tasks:
                    raise Exception('duplicate task key found: {0}'.format(k))
            tasks.update(exported)
        return tasks


class TaskTemplates(object):
    def __init__(self, config, targets):
        self.entries = []
        for target_id, entry in config.items():
            if '__plain__' == target_id:
                self.entries.append(entry)
            else:
                target = targets.get_target(target_id)
                self.entries.append(TaskTemplate(entry, target.get_contexts()))

    def render(self):
        tasks = OrderedDict()
        for task in self.entries:
            if isinstance(task, list):
                for entry in task:
                    for k in entry:
                        if k in tasks:
                            raise Exception('duplicate task key found: {0}'
                                            .format(k))
                        tasks[k] = entry[k]
            else:
                exported = task.render()
                for k in exported:
                    if k in tasks:
                        raise Exception('duplicate task key found: {0}'
                                        .format(k))
                    tasks[k] = exported[k]
        return tasks


class TaskTemplate(object):
    def __init__(self, config, contexts):
        self.entries = [
            TaskTemplateEntry(template, contexts)
            for template in config]

    def render(self):
        tasks = OrderedDict()
        for task in self.entries:
            exported = task.render()
            for k in exported:
                if k in tasks:
                    raise Exception('duplicate task key found: {0}'.format(k))
            tasks.update(exported)
        return tasks


class TaskTemplateEntry(object):
    def __init__(self, config, contexts):
        self.contexts = contexts
        if 'name' in config:
            self.name = config['name']
            self.subtasks = config['subtasks']
        else:
            self.name = next(iter(config.keys()))
            self.subtasks = config[self.name]
        self.render_name = Environment().from_string(self.name).render
        self.subtasks = ListTemplate(self.subtasks)

    def render(self):
        tasks = OrderedDict()
        for context in self.contexts:
            name = str(self.render_name(**context))
            if name not in tasks:
                tasks[name] = []
            subtasks = self.subtasks.render(**context)
            tasks[name].extend(subtasks)
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


def generate_tasks(tasks, **context):
    if isinstance(tasks, six.string_types):
        tasks = yamlutil.load_dict(tasks)
    tasks.update(context)
    return Definitions(tasks).tasks.render()


def main():
    import os
    import sys
    import json
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('filename', nargs='+')
    args.add_argument('-k', dest='key', required=False)
    args = args.parse_args()

    tasks = []
    for filename in args.filename:
        filename = os.path.abspath(filename)
        with open(filename) as f:
            tasks.append(f.read())
    tasks = os.linesep.join(tasks)
    tasks = yamlutil.load_dict(tasks)

    config = Definitions(tasks)
    if args.key is not None:
        sys.stdout.write(yamlutil.dump_dict(
            config.tasks.get_templates(args.key).render()))
    else:
        sys.stdout.write(yamlutil.dump_dict(config.tasks.render()))


if '__main__' == __name__:
    main()
