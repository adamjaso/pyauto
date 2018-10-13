import os
import sys
from unittest import TestCase
from pyauto.core import tool, api
from subprocess import Popen, PIPE
from pyauto.util import yamlutil

dirname = os.path.dirname(os.path.abspath(__file__))
example = os.path.join(dirname, 'objects-example')


with open(os.path.join(example, 'kinds.yml')) as f:
    packages = [pkg for pkg in yamlutil.load_dict(f, load_all=True)]


def login(region, **args):
    print('login')
    pass


def run_tool(objects, tasks, kinds, cmd, *args):
    objects = os.path.join(example, objects)
    tasks = os.path.join(example, tasks)
    kinds = os.path.join(example, kinds)
    p = Popen(['python', '-m', 'pyauto.core.tool',
               '-o', objects, '-t', tasks, '-p', kinds, cmd] + list(args),
               stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    print('STDERR:', stderr.decode('utf-8'))
    print('STDOUT:', stdout.decode('utf-8'))
    return p


class Region(api.KindObject):
    pass


class Cli(TestCase):
    def test_run_files(self):
        p = run_tool('objects.yml', 'tasks.yml', 'pkg.yml', 'run', '{reg:{tags:[r1]}}', 'regions_login')
        self.assertEqual(p.returncode, 0)

    def test_run_dirs(self):
        p = run_tool('objects', 'tasks.yml', 'pkg.yml', 'run', '{reg:{tags:[r1]}}', 'regions_login')
        self.assertEqual(p.returncode, 0)

    def test_query_dirs(self):
        p = run_tool('objects', 'tasks.yml', 'pkg.yml', 'query', '{test.Region:{tags:[r1]}}')
        self.assertEqual(p.returncode, 0)

