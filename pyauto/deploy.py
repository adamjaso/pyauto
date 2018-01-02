import os
import argparse
from . import config as pyauto_config


def main():
    args = argparse.ArgumentParser()
    args.add_argument('-c', '--config', dest='config', required=True)
    args.add_argument('-q', '--quiet', dest='quiet', action='store_true')
    args.add_argument('-i', '--inspect', dest='inspect', action='store_true')
    args.add_argument('-t', '--tree', dest='tree', action='store_true')
    args.add_argument('action', nargs='*')
    args = args.parse_args()

    config_file = os.path.abspath(args.config)
    config = pyauto_config.load(config_file)
    config.run_task_sequences(
        *args.action,
        quiet=args.quiet,
        inspect=args.inspect,
        tree=args.tree)


if '__main__' == __name__:
    main()
