import os
import argparse
from . import config as pyauto_config


class Command(object):
    config = None
    dirname = None
    action = None
    quiet = None
    inspect = None
    tree = None

    def __init__(self, config, action,
                 quiet=None, inspect=None, tree=None, dirname=None):
        if dirname is None:
            dirname = os.path.dirname(os.path.abspath(config))
        self.config = pyauto_config.load(
            os.path.abspath(config), dirname=dirname)
        self.action = action or []
        self.quiet = quiet
        self.inspect = inspect
        self.tree = tree

    @classmethod
    def from_args(cls):
        args = argparse.ArgumentParser()
        args.add_argument('-c', '--config', dest='config', required=True)
        args.add_argument('-q', '--quiet', dest='quiet', action='store_true')
        args.add_argument('-i', '--inspect',
                          dest='inspect', action='store_true')
        args.add_argument('-t', '--tree', dest='tree', action='store_true')
        args.add_argument('-o', '--output', dest='output_dir')
        args.add_argument('action', nargs='*')
        args = args.parse_args()
        return cls(args.config, args.action,
                   quiet=args.quiet, inspect=args.inspect, tree=args.tree,
                   dirname=args.output_dir)

    def execute(self):
        return self.config.run_task_sequences(
            *self.action,
            quiet=self.quiet,
            inspect=self.inspect,
            tree=self.tree)


def main():
    return Command.from_args().execute()


if '__main__' == __name__:
    main()
