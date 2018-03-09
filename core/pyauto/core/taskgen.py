import six
import itertools
from jinja2 import Environment
from collections import OrderedDict


class TaskGenerator(object):
    list_templates = None
    task_templates = None
    columns = None
    foreach = None
    foreach_items = None
    foreach_contexts = None
    foreach_product = None

    def __init__(self, config, parent):
        self.list_templates = {
            key: TaskTemplateList(template_list)
            for key, template_list in config.get('list_templates', {}).items()}
        self.task_templates = [
            TaskTemplate(template_task, self)
            for template_task in config.get('task_templates', [])]
        self.columns = config.get('columns', [])
        self.foreach = config.get('foreach', [])
        self.foreach_items = []
        for key in self.foreach:
            if not isinstance(key, six.string_types) and isinstance(key, list):
                self.foreach_items.append(key)
            elif key not in parent:
                raise Exception('"{0}" key not found'.format(key))
            else:
                self.foreach_items.append(parent[key])
        self.foreach_product = [
            list(row) for row in itertools.product(*self.foreach_items)]
        self.foreach_contexts = []
        for row in self.foreach_product:
            context = dict(zip(self.columns, row))
            self.foreach_contexts.append(context)

    def get_foreach_context(self, column=None):
        if column is not None:
            for i, name in enumerate(self.columns):
                if name == column:
                    return [{column: item} for item in self.foreach_items[i]]
            raise Exception('unknown context: "{0}"'.format(column))
        else:
            return self.foreach_contexts

    def render(self):
        tasks = OrderedDict()
        for export_task in self.task_templates:
            exported = export_task.render()
            for k in exported:
                if k in tasks:
                    raise Exception('duplicate task key found: {0}'.format(k))
            tasks.update(exported)
        return tasks


class TaskTemplateList(object):
    def __init__(self, task_list):
        env = Environment()
        self.task_list = [
            env.from_string(task_template).render
            for task_template in task_list
        ]

    def render(self, **context):
        return [str(render(**context)) for render in self.task_list]


class TaskTemplate(object):
    def __init__(self, config, parent):
        self.config = parent
        self._dict = config
        env = Environment()
        self.column = config.get('column')
        if 'name' in config:
            self.name = config['name']
            self.subtasks = config['subtasks']
        else:
            self.name = next(iter(config.keys()))
            self.subtasks = config[self.name]
        self.render_name = env.from_string(self.name).render
        if isinstance(self.subtasks, six.string_types):
            self.task_template_list = parent.list_templates[self.subtasks]
        else:
            self.task_template_list = TaskTemplateList(self.subtasks)

    def render(self):
        tasks = OrderedDict()
        contexts = self.config.get_foreach_context(self.column)
        for context in contexts:
            name = str(self.render_name(**context))
            if name not in tasks:
                tasks[name] = []
            task_list = self.task_template_list.render(**context)
            tasks[name].extend(task_list)
        return tasks


def generate_tasks(tasks, **context):
    return TaskGenerator(tasks, context).render()


def main():
    import os
    import argparse
    from pyauto.util import yamlutil
    args = argparse.ArgumentParser()
    args.add_argument('-t', '--template', dest='template', required=True)
    args.add_argument('-v', '--values', dest='values', default=None)
    args.add_argument('-k', '--key', dest='key', required=True)
    args = args.parse_args()

    template_file = os.path.abspath(args.template)

    if args.values:
        values_file = os.path.abspath(args.values)
        with open(values_file) as f:
            values = yamlutil.load_dict(f.read())
    else:
        values = None
    with open(template_file) as f:
        template = yamlutil.load_dict(f.read())
    if values is None:
        values = template
    rendered = generate_tasks(template[args.key], **values)
    print(yamlutil.dump_dict(rendered))


if '__main__' == __name__:
    main()
