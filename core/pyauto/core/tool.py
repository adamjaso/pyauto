import os
import sys
import json
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
        args = yamlutil.load_dict(args or '{}')
        ref = api.TaskReference(kind_task)
        return self.repository.invoke_kind_task(ref.kind, tag, ref.name, args)

    def show_files(self):
        data = OrderedDict([
            ('Kinds', OrderedDict([
                ('filename', self.packages_filename),
                ('names', [
                    OrderedDict([
                        ('name', k.name),
                        ('commands', str(
                            self.repository[k.name].kind.command_class)),
                        ('configs', str(
                            self.repository[k.name].kind.config_class))
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

    def run_query(self, args):
        q = yamlutil.load_dict(args.selector)
        res = self.repository.query(q, id=True, match=args.match)
        if args.verbose:
            res = [self.repository[tag].data for tag in res]
        logger.debug(yamlutil.dump_dict([o for o in res]).strip())

    def invoke_task(self, args):
        parts = args.task.split(':')
        if 'cmd' == parts[0]:
            res = self.invoke_kind_task(parts[1], args.targets, args.args)
            res = render_output(args.format, res)
            logger.debug(res)

        elif 'task' == parts[0]:
            for res in self.invoke_task_sequence(args.targets, parts[1],
                                                 inspect=args.inspect):
                res = render_output(args.format, res)
                logger.debug(res)
        else:
            raise api.InvalidKindObjectTaskInvocationException(
                'Invalid kind object task: {0}'.format(args.task))

    def dump(self, args):
        if args.packages:
            for item in self.repository.dump_packages():
                sys.stdout.write('---' + os.linesep)
                data = yamlutil.dump_dict(item)
                sys.stdout.write(data)
            sys.stdout.flush()
        else:
            for item in self.repository.dump():
                sys.stdout.write('---' + os.linesep)
                data = yamlutil.dump_dict(item)
                sys.stdout.write(data)
            sys.stdout.flush()


def render_output(format, data):
    if 'prettyjson' == format:
        return json.dumps(data, indent=2)
    elif 'json' == format:
        return json.dumps(data)
    elif 'yaml' == format:
        return yamlutil.dump_dict([data])
    elif 'text' == format:
        return str(data)
    else:
        raise api.PyautoException('Invalid output format: {0}'.format(format))


def main():
    setup_logger(logger)
    args = argparse.ArgumentParser()
    args.add_argument('-d', dest='dirname')
    args.add_argument('-o', dest='objects_filename', required=True)
    args.add_argument('-t', dest='tasks_filename', required=True)
    args.add_argument('-p', dest='packages_filename', required=True)
    args.add_argument('-f', '--format', dest='format', choices=[
        'yaml', 'json', 'prettyjson'], default='yaml')

    parsers = args.add_subparsers(dest='action')
    run = parsers.add_parser('run')
    run.add_argument('targets')
    run.add_argument('task')
    run.add_argument('-a', '--args', dest='args', default='{}',
                     type=yamlutil.load_dict)
    run.add_argument('-i', '--inspect', dest='inspect', action='store_true')
    query = parsers.add_parser('query')
    query.add_argument('selector')
    query.add_argument('-m', '--match', dest='match', choices=['tags', 'labels'], default='tags')
    query.add_argument('-v', '--verbose', dest='verbose', action='store_true')
    dump = parsers.add_parser('dump')
    dump.add_argument('--packages', action='store_true')
    args = args.parse_args()

    r = api.Repository()
    cmd = Command(r, args.objects_filename, args.packages_filename,
                  args.tasks_filename, dirname=args.dirname)
    cmd.validate_files()
    cmd.load()
    if 'run' == args.action:
        cmd.invoke_task(args)
    elif 'query' == args.action:
        cmd.run_query(args)
    elif 'dump' == args.action:
        cmd.dump(args)
    else:
        cmd.show_files()


if '__main__' == __name__:
    main()
