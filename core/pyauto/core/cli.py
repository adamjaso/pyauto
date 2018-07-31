import os
import sys
import argparse
from collections import OrderedDict
from pyauto.util import yamlutil
from . import objects


def write(*args):
    sys.stdout.write(' '.join([str(arg) for arg in args]))
    sys.stdout.flush()


class Command(object):
    repository = None
    tasks = None
    objects_filename = None
    packages_filename = None
    tasks_filename = None

    def __init__(self, repository, objects_filename,
                 packages_filename, tasks_filename, dirname=None):
        self.repository = repository
        if dirname is not None:
            objects_filename = os.path.join(dirname, objects_filename)
            tasks_filename = os.path.join(dirname, tasks_filename)
            if packages_filename is not None:
                packages_filename = os.path.join(dirname, packages_filename)
        self.objects_filename = os.path.abspath(objects_filename)
        self.tasks_filename = os.path.abspath(tasks_filename)
        if packages_filename is not None:
            self.packages_filename = os.path.abspath(packages_filename)

    def validate_files(self):
        errors = []
        try:
            os.stat(self.objects_filename)
        except:
            errors.append('Objects file not found: {0}'
                          .format(self.objects_filename))
        try:
            os.stat(self.packages_filename)
        except:
            errors.append('Packages file not found: {0}'
                          .format(self.packages_filename))
        if self.tasks_filename is not None:
            try:
                os.stat(self.tasks_filename)
            except:
                errors.append('Tasks file not found: {0}'
                              .format(self.tasks_filename))
        if len(errors) > 0:
            print(os.linesep.join(errors))
            sys.exit(1)

    def load(self):
        self.read_packages()
        self.read_objects()
        self.read_tasks()

    def read_packages(self):
        if self.packages_filename is not None:
            for obj in self.read_filename(self.packages_filename):
                self.repository.add_package(obj)
        for kind in self.repository.kinds:
            if kind.has_module():
                mod = kind.get_module()
                kindobjs = getattr(mod, 'kinds', [])
                if not isinstance(kindobjs, list):
                    raise objects.PyautoException(
                        'Module kinds must be provided as a list: {0}.kinds = {1}'
                        .format(mod.__name__, kindobjs))
                for kindobj in kindobjs:
                    self.repository.add_package(kindobj)

    def read_objects(self):
        for obj in self.read_filename(self.objects_filename):
            self.repository.add(obj)

    def read_tasks(self):
        with open(self.tasks_filename) as f:
            tasks = yamlutil.load_dict(f)
        self.tasks = objects.TaskSequences(self.repository, tasks)

    def read_filename(self, fn):
        if os.path.isfile(fn):
            with open(fn) as f:
                for item in yamlutil.load_dict(f, load_all=True):
                    if isinstance(item, list):
                        for obj in item:
                            yield obj
                    else:
                        yield item
        elif os.path.isdir(fn):
            for dirpath, dirnames, filenames in os.walk(fn):
                for filename in filenames:
                    filename = os.path.join(dirpath, filename)
                    with open(filename) as f:
                        for item in yamlutil.load_dict(f, load_all=True):
                            if isinstance(item, list):
                                for obj in item:
                                    yield obj
                            else:
                                yield item
        else:
            raise objects.PyautoException('Not a file or directory: {0}'
                                          .format(fn))

    def invoke_task_sequence(self, targets, task):
        obj = yamlutil.load_dict(targets)
        return self.tasks[task].invoke(obj)

    def show_files(self):
        data = OrderedDict([
            ('Kinds', OrderedDict([
                ('filename', self.packages_filename),
                ('names', [
                    OrderedDict([
                        ('name', k.name),
                        ('module', str(self.repository[k.name]\
                                           .kind.get_module()))
                    ])
                    for k in self.repository.kinds
                ]),
            ])),
            ('Objects', OrderedDict([
                ('filename', self.objects_filename),
                ('kinds', OrderedDict([
                    (k.name, len(self.repository[k.name]))
                    for k in self.repository.kinds
                ])),
            ])),
            ('Tasks', OrderedDict([
                ('filename', self.tasks_filename),
                ('names', [
                    name for name, _ in self.tasks.items()])
            ])),
        ])
        write(yamlutil.dump_dict(data))

    def run_query(self, selector):
        q = yamlutil.load_dict(selector)
        res = self.repository.query(q, id=True)
        write(yamlutil.dump_dict([o for o in res]))


def main():
    args = argparse.ArgumentParser()
    args.add_argument('-d', dest='dirname')
    args.add_argument('-o', dest='objects_filename', required=True)
    args.add_argument('-t', dest='tasks_filename', required=True)
    args.add_argument('-p', dest='packages_filename', required=True)

    parsers = args.add_subparsers(dest='action')
    run = parsers.add_parser('run')
    run.add_argument('targets')
    run.add_argument('task')
    query = parsers.add_parser('query')
    query.add_argument('selector')
    args = args.parse_args()

    r = objects.Repository()
    cmd = Command(r, args.objects_filename, args.packages_filename,
                  args.tasks_filename, dirname=args.dirname)
    cmd.validate_files()
    cmd.load()
    if 'run' == args.action:
        cmd.invoke_task_sequence(args.targets, args.task)
    elif 'query' == args.action:
        cmd.run_query(args.selector)
    else:
        cmd.show_files()


if '__main__' == __name__:
    main()
