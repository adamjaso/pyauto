import os, shutil, six, subprocess, sys
from unittest import TestCase
from pyauto.core import api
from pyauto.local import config as local_config
from pyauto.shell import config as shell_config

dirname = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
repo = api.Repository()
for pkg in shell_config.packages:
    repo.add_package(pkg)
for pkg in local_config.packages:
    repo.add_package(pkg)
for obj in api.read_packages(__file__, 'config.yml'):
    repo.add(obj)


class Command(TestCase):
    def tearDown(self):
        for fn in ['output.1', 'output.2']:
            if os.path.isfile(fn):
                os.remove(fn)

    def test_describe_command(self):
        cmd = repo['shell.Command/show-home-1']
        # FIXME: just make sure we can call it and it doesn't blow up
        cmd.describe_command()

    def test_run_command(self):
        cmd = repo['shell.Command/show-home-1']
        # FIXME: just make sure we can call it and it doesn't blow up
        cmd.run_command()

    def test_run_command_with_directory(self):
        cmd = repo['shell.Command/generate-rsa-key']
        cmd.run_command()
        cmd = repo['shell.Command/public-rsa-key']
        cmd.run_command()
        self.assertTrue(os.path.isfile('test/public.out'))
        os.remove('test/public.out')
        os.remove('test/private.key')

    def test_custom_env(self):
        cmd = repo['shell.Command/customenv']
        cmd.run_command()
