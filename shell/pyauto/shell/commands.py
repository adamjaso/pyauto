import os
import pyauto.shell.config


def list_commands(config):
    return os.linesep.join([sh.tag for sh in config.shell.__iter__()])


def describe_command(config, shell_tag):
    return config.shell.get_tag(shell_tag).get_command_description()


def run_command(config, shell_tag):
    return config.shell.get_tag(shell_tag)\
            .run_command(verbose=True).returncode


def get_command_output(config, shell_tag):
    return config.shell.get_tag(shell_tag)\
            .run_command(verbose=False, capture_output=True).stdout

