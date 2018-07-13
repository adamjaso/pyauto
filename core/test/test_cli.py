import os
import sys
from unittest import TestCase
from pyauto.core import cli
from subprocess import Popen, PIPE

dirname = os.path.dirname(os.path.abspath(__file__))
example = os.path.join(dirname, 'objects-example')


def login(region, **args):
    print('login')
    pass


def run_cli(objects, tasks, kinds, cmd, *args):
    objects = os.path.join(example, objects)
    tasks = os.path.join(example, tasks)
    kinds = os.path.join(example, kinds)
    p = Popen(['python', '-m', 'pyauto.core.cli',
                  '-o', objects, '-t', tasks, '-k', kinds, cmd] + list(args),
                  stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    print('STDERR:', stderr.decode('utf-8'))
    print('STDOUT:', stdout.decode('utf-8'))
    return p


class Cli(TestCase):
    def test_run_files(self):
        p = run_cli('objects.yml', 'tasks.yml', 'kinds.yml', 'run', '{reg:[r1]}', 'regions.login')
        self.assertEqual(p.returncode, 0)

    def test_run_dirs(self):
        p = run_cli('objects', 'tasks.yml', 'kinds', 'run', '{reg:[r1]}', 'regions.login')
        self.assertEqual(p.returncode, 0)

    def test_query_dirs(self):
        p = run_cli('objects', 'tasks.yml', 'kinds', 'query', '{obj.Region:[r1]}')
