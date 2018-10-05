import os
import sys
import logging
import argparse
import importlib
from logging import StreamHandler
from collections import OrderedDict
from pyauto.util import yamlutil
from . import api


logger = logging.getLogger('pyauto.core')


def setup_logger(logger):
    formatter = logging.Formatter('%(message)s')
    handler = StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


def write(*args):
    sys.stdout.write(' '.join([str(arg) for arg in args]))
    sys.stdout.flush()


class Packages(object):
    def __init__(self, data):
        self.module = importlib.import_module(data['module'])
        if not hasattr(self.module, 'packages'):
            raise api.PyautoException(
                'Module is not a package: "{0}"'
                .format(data['module']))
        if not isinstance(self.module.packages, list):
            raise api.PyautoException(
                'Module "packages" is not a list: "{0}"'
                .format(self.module.packages))
        self.data = self.module.packages

    def __iter__(self):
        for item in self.data:
            yield item


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
            for package in self._read_packages(self.packages_filename):
                self.repository.add_package(package)

    def read_objects(self):
        for obj in api.read_packages(self.objects_filename):
            self.repository.add(obj)

    def read_tasks(self):
        with open(self.tasks_filename) as f:
            tasks = yamlutil.load_dict(f)
        self.tasks = api.TaskSequences(self.repository, tasks)

    def _read_packages(self, fn):
        with open(fn) as f:
            data = yamlutil.load_dict(f)
            for item in data['packages']:
                for pkg in Packages(item):
                    yield pkg

    def invoke_task_sequence(self, targets, task, inspect=False):
        obj = yamlutil.load_dict(targets)
        return self.tasks[task].invoke(obj, inspect=inspect)

    def invoke_kind_task(self, kind_task, tag, args):
        ref = api.TaskReference(kind_task)
        obj = self.repository[ref.kind][tag]
        args = yamlutil.load_dict(args or '{}')
        return self.repository[ref.kind].kind.tasks[ref.name].invoke(obj, **args)

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
        logger.debug(yamlutil.dump_dict(data))

    def run_query(self, selector, verbose):
        q = yamlutil.load_dict(selector)
        res = self.repository.query(q, id=True)
        if verbose:
            res = [self.repository[tag].data for tag in res]
        logger.debug(yamlutil.dump_dict([o for o in res]))

    def invoke_task(self, args):
        parts = args.task.split(':')
        if 'cmd' == parts[0]:
            res = self.invoke_kind_task(parts[1], args.targets, args.args)
            logger.debug(res)

        elif 'task' == parts[0]:
            for res in self.invoke_task_sequence(args.targets, parts[1],
                                                 inspect=args.inspect):
                logger.debug(yamlutil.dump_dict([res]))


def main():
    setup_logger(logger)
    args = argparse.ArgumentParser()
    args.add_argument('-d', dest='dirname')
    args.add_argument('-o', dest='objects_filename', required=True)
    args.add_argument('-t', dest='tasks_filename', required=True)
    args.add_argument('-p', dest='packages_filename', required=True)

    parsers = args.add_subparsers(dest='action')
    run = parsers.add_parser('run')
    run.add_argument('targets')
    run.add_argument('task')
    run.add_argument('-a', '--args', dest='args', default='{}',
                     type=yamlutil.load_dict)
    run.add_argument('-i', '--inspect', dest='inspect', action='store_true')
    query = parsers.add_parser('query')
    query.add_argument('selector')
    query.add_argument('-v', '--verbose', dest='verbose', action='store_true')
    args = args.parse_args()

    r = api.Repository()
    cmd = Command(r, args.objects_filename, args.packages_filename,
                  args.tasks_filename, dirname=args.dirname)
    cmd.validate_files()
    cmd.load()
    if 'run' == args.action:
        cmd.invoke_task(args)
    elif 'query' == args.action:
        cmd.run_query(args.selector, args.verbose)
    else:
        cmd.show_files()


if '__main__' == __name__:
    main()