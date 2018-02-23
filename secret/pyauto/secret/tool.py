import os
import sys
import json
import shlex
import shutil
import importlib
from pyauto.util import yamlutil
from .store import Store, GroupDefinition


def parse_owner(owner):
    owner, profile = owner.split(':', 1)
    owner = owner.split('/', 1)
    return [owner, profile]


def parse_key(key):
    key = key.split('/', 3)
    if len(key) not in [3, 4]:
        raise Exception('Invalid key: {0}. Cannot parse'.format(key))
    if len(key) == 3:
        key.append(None)
    else:
        key[3] = key[3].split(',')
    return key


def main():
    import argparse

    args = argparse.ArgumentParser()
    args.add_argument('-d', '--definitions-file',
                      dest='definitions_file', required=True)
    args.add_argument('-f', '--store-file',
                      dest='store_file', required=True)
    args.add_argument('-F', '--definitions-format',
                      dest='definitions_format', default='yaml',
                      choices=['yaml', 'json'], required=False)
    args.add_argument('key')
    args.add_argument('action', choices=['generate', 'delete'])
    args.add_argument('--show', dest='show', action='store_true')
    args = args.parse_args()

    store_file = os.path.abspath(args.store_file)
    definitions_file = os.path.abspath(args.definitions_file)
    group_def = GroupDefinition.parse_definitions_file(
        definitions_file, args.definitions_format)
    try:
        store = Store(store_file)
        if 'delete' == args.action:
            key = parse_key(args.key)
            store.delete_keys(*key)
        elif 'generate' == args.action:
            owner = parse_owner(args.key)
            profile = owner[1]
            owner_type, owner = owner[0]
            values = store.get_group(owner_type, owner)\
                 .get_dict(group_def[profile].definition)
        if args.show:
            with open(store_file) as f:
                shutil.copyfileobj(f, sys.stdout)
    except ModuleNotFoundError as e:
        sys.exit(str(e))


if '__main__' == __name__:
    main()
