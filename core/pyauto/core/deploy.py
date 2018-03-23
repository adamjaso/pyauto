from __future__ import print_function
import os
import sys
import time
import argparse
import signal
from . import config as pyauto_config
from multiprocessing import Process
from datetime import datetime


class Command(object):
    config = None
    dirname = None
    action = None
    quiet = None
    inspect = None
    tree = None

    def __init__(self, config, action,
                 quiet=None, inspect=None, tree=None, dirname=None,
                 parallel=None):
        if dirname is None:
            dirname = os.path.dirname(os.path.abspath(config))
        self.config_file = os.path.abspath(config)
        self.config = pyauto_config.load(
            self.config_file, dirname=dirname)
        self.action = action or []
        self.quiet = quiet
        self.inspect = inspect
        self.tree = tree
        if parallel is None:
            self.parallel = None
        else:
            if len(self.action) == 1:
                task_seqs = self.config\
                    .get_task_sequence(self.action[0]).task_list
                action = [task_seq.task_name for task_seq in task_seqs]
            else:
                action = self.action
            self.parallel = ParallelCommand(
                self.config_file, parallel, action)

    @classmethod
    def from_args(cls, **kwargs):
        args = argparse.ArgumentParser()
        args.add_argument('-c', '--config', dest='config', required=True)
        args.add_argument('-q', '--quiet', dest='quiet', action='store_true')
        args.add_argument('-i', '--inspect',
                          dest='inspect', action='store_true')
        args.add_argument('-t', '--tree', dest='tree', action='store_true')
        args.add_argument('-o', '--output', dest='output_dir')
#        args.add_argument('--log-file', dest='log_file')
        args.add_argument('--parallel', dest='parallel')
        args.add_argument('action', nargs='*')
        args = args.parse_args(**kwargs)
        return cls(args.config, args.action,
                   quiet=args.quiet, inspect=args.inspect, tree=args.tree,
                   dirname=args.output_dir, parallel=args.parallel)

    def execute(self):
        if self.parallel:
            return self.parallel.execute()
        else:
            return self.config.run_task_sequences(
                *self.action,
                quiet=self.quiet,
                inspect=self.inspect,
                tree=self.tree)


class ParallelCommand(object):
    def __init__(self, config_file, parallel_dir, actions, **kwargs):
        self.job_name = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        self.config_file = os.path.abspath(config_file)
        self.parallel_dir = os.path.join(
            os.path.abspath(parallel_dir), self.job_name)
        self.actions = actions

    def get_action_log_file(self, action):
        if not os.path.isdir(self.parallel_dir):
            os.makedirs(self.parallel_dir)
        return os.path.join(self.parallel_dir, '.'.join([action, 'txt']))

    def execute(self):
        processes = []

        def async_task(config_file, action, log_file):
            if log_file is not None:
                logs = open(log_file, 'w')
                sys.stdout = logs
                sys.stderr = logs
            return Command(config_file, [action]).execute()

        def process_status(process, message=None):
            if process.exitcode is not None:
                print('Task "{0}" ({1}) completed with code {2}.'.format(
                    process.name, process.pid, process.exitcode))
            elif message:
                print('Task "{0}" ({1}) {2}'.format(
                    process.name, process.pid, message))
            else:
                print('Task "{0}" ({1}) is running...'.format(
                    process.name, process.pid))

        def signal_handler(signum, frame):
            print('-----', datetime.now(), '-----')
            for process in processes:
                process_status(process, 'stopping...')
            for process in processes:
                process.terminate()
                process.join()
                process_status(process)
            sys.exit(1)

        signal.signal(signal.SIGINT, signal_handler)

        for action in self.actions:
            log_file = self.get_action_log_file(action)
            process = Process(
                target=async_task,
                name='-'.join([self.job_name, action]),
                args=(self.config_file, action, log_file))
            processes.append(process)

        print('-----', datetime.now(), '-----')
        for process in processes:
            process.start()
            process_status(process)

        while len(processes) > 0:
            time.sleep(1)
            print('-----', datetime.now(), '-----')
            for i, process in reversed(list(enumerate(processes))):
                process_status(process)
                if process.exitcode is not None:
                    process.join()
                    del processes[i]


def main():
    return Command.from_args().execute()


if '__main__' == __name__:
    main()
