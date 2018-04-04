import os, shutil, six, subprocess, sys
from unittest import TestCase
from pyauto.core import deploy, config as core_config
from pyauto.local import config as local_config
from pyauto.shell import config as shell_config

dirname = os.path.dirname(os.path.abspath(__file__))
conf = deploy.Command(os.path.join(dirname, 'config.yml'), []).config
shell = conf.shell
local = conf.local

def get_shell_config():
    return shell_config.Shell.wrap([
        {'tag': 'cmd-1',
         'directory': '.',
         'success_codes': [0, 100],
         'command': 'pwd',
         'stdout': 'out.1',
         'custom_env': {
            'TEST': 'abc123',
         }},
        {'tag': 'cmd-2',
         'directory_resource': 'local/get_destination_path,home',
         'command': 'ls -la'},
        {'tag': 'cmd-3',
         'directory': './workspace',
         'command': 'pwd'},
        {'tag': 'cmd-4',
         'directory_local': 'home',
         'command': 'pwd'},
    ], conf)


class Shell(TestCase):
    def test_get_command_description(self):
        expected = [
            item.format(dirname) for item in
            ['shell "cmd-1" runs command "pwd" in directory "{0}", saving '
             'stdout in "{0}/out.1" and stderr in "&2"'.format(os.getcwd()),

             'shell "cmd-2" runs command "ls -la" in directory '
             '"{0}/workspace/.", saving stdout in "&1" and stderr in "&2"',

             'shell "cmd-3" runs command "pwd" in directory "{0}/workspace", '
             'saving stdout in "&1" and stderr in "&2"'.format(os.getcwd()),

             'shell "cmd-4" runs command "pwd" in directory '
             '"{0}/workspace/.", saving stdout in "&1" and stderr in "&2"'
            ]]
        for sh in get_shell_config().__iter__():
            description = sh.get_command_description()
            self.assertIn(description, expected)

    def test_get_command_string(self):
        self.assertEqual(
            'ls -la', get_shell_config().get_tag('cmd-2').get_command_string())

    def test_start(self):
        sh = get_shell_config().get_tag('cmd-2')
        p = sh.start()
        self.assertIsNone(p.returncode)
        self.assertIsInstance(p, subprocess.Popen)

    def test_run_command(self):
        sh = get_shell_config().get_tag('cmd-2')
        r = sh.run_command(verbose=True, capture_output=True)
        self.assertIsInstance(r, shell_config.ProcessResult)
        self.assertEqual(len(r.stdout.split('\n')), 4)

    def test_get_success_codes(self):
        sh = get_shell_config().get_tag('cmd-1')
        codes = sh.get_success_codes()
        self.assertListEqual(codes, [0, 100])

    def test_get_custom_env(self):
        sh = get_shell_config().get_tag('cmd-2')
        self.assertIsNone(sh.get_custom_env())
        sh = get_shell_config().get_tag('cmd-1')
        self.assertDictEqual(sh.get_custom_env(), {'TEST': 'abc123'})

    def test_stdout_stderr_name(self):
        sh = get_shell_config().get_tag('cmd-1')
        stdout_name = sh.get_stdout_name()
        self.assertEqual('{0}/out.1'.format(os.getcwd()), stdout_name)
        stderr_name = sh.get_stderr_name()
        self.assertEqual('&2', stderr_name)

    def test_get_stdin(self):
        sh = get_shell_config().get_tag('cmd-1')
        sh.get_stdin()

    def test_get_stdout(self):
        sh = get_shell_config().get_tag('cmd-1')
        f = sh.get_stdout()
        if f != sys.stdout:
            f.close()

    def test_get_stderr(self):
        sh = get_shell_config().get_tag('cmd-1')
        f = sh.get_stderr()
        if f != sys.stderr:
            f.close()

    def test_get_directory(self):
        sh = get_shell_config().get_tag('cmd-2')
        self.assertEqual(os.path.join(dirname, 'workspace/.'),
                         sh.get_directory())
        sh = get_shell_config().get_tag('cmd-3')
        self.assertEqual(os.path.abspath('workspace'), sh.get_directory())
        sh = get_shell_config().get_tag('cmd-4')
        self.assertEqual(os.path.join(dirname, 'workspace/.'),
                         sh.get_directory())

