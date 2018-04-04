import os
import six
import sys
from subprocess import Popen, PIPE
from pyauto.core import config
from pyauto.util.strutil import root_prefix


def log(*args):
    sys.stdout.write(' '.join([str(a) for a in args]) + os.linesep)
    sys.stdout.flush()


class ProcessResult(object):
    def __init__(self, p, stdout, stderr):
        self.pid = p.pid
        self.returncode = p.returncode
        self.stdout = stdout
        self.stderr = stderr


class Shell(config.Config):
    def get_command_description(self):
        return ('shell "{0}" runs command "{1}" in directory "{2}", saving '
                'stdout in "{3}" and stderr in "{4}"'.format(
                    self.tag, self.get_command_string(), self.get_directory(),
                    self.get_stdout_name(), self.get_stderr_name()))

    def get_command_string(self):
        return self.command

    def start(self, capture_output=False):
        return Popen(
            self.command,
            shell=True,
            stdin=self.get_stdin(),
            stdout=self.get_stdout(capture_output),
            stderr=self.get_stderr(capture_output),
            env=self.get_custom_env(),
            cwd=self.get_directory(),
        )

    def run_command(self, verbose=True, capture_output=False):
        if verbose:
            log('starting shell "{0}" with args "{1}" in directory "{2}"...'
                .format(self.tag, self.get_command_string(),
                        self.get_directory()))
        p = self.start(capture_output)
        if verbose:
            log('started shell "{0}" with pid "{1}"'
                .format(self.tag, p.pid))
        if capture_output:
            stdout, stderr = p.communicate()
            if six.PY3 and isinstance(stdout, six.binary_type):
                stdout = stdout.decode('utf-8')
                stderr = stderr.decode('utf-8')
            if stderr:
                sys.stderr.write(stderr + os.linesep)
                sys.stderr.flush()
        else:
            stdout, stderr = None, None
            p.wait()
        if verbose:
            log('finished shell "{0}" with pid "{1}" returned code "{2}"'
                .format(self.tag, p.pid, p.returncode))
        if p.returncode not in self.get_success_codes():
            raise Exception('shell command "{0}" failed with return code "{1}"'
                            .format(self.tag, p.returncode))
        return ProcessResult(p, stdout, stderr)

    def get_success_codes(self):
        return self.get('success_codes', [0])

    def get_custom_env(self):
        return self.get('custom_env', None)

    def _get_pipe_name(self, name, default):
        value = self.get(name, '')
        if '' == value:
            return default
        elif value.startswith(root_prefix):
            return value
        else:
            return os.path.join(self.get_directory(), value)

    def get_stdin_name(self):
        return self._get_pipe_name('stdin', '&0')

    def get_stdin(self):
        name = self.get_stdin_name()
        if '&0' == name:
            return sys.stdin
        else:
            return open(name, 'rb')

    def get_stdout_name(self):
        return self._get_pipe_name('stdout', '&1')

    def get_stdout(self, capture_output=False):
        if capture_output:
            return PIPE
        name = self.get_stdout_name()
        if '&1' == name:
            return sys.stdout
        else:
            return open(name, 'wb')

    def get_stderr_name(self):
        return self._get_pipe_name('stderr', '&2')

    def get_stderr(self, capture_output=False):
        if capture_output:
            return PIPE
        name = self.get_stderr_name()
        if '&2' == name:
            return sys.stderr
        else:
            return open(name, 'wb')

    def get_directory(self):
        if self.directory:
            return os.path.abspath(os.path.expanduser(self.directory))
        elif self.directory_resource:
            return self.config.get_resource(self.directory_resource)
        elif self.directory_local:
            return os.path.expanduser(
                self.config.local.get_destination_path(self.directory_local))
        else:
            return os.getcwd()


config.set_config_class('shell', Shell.wrap)
