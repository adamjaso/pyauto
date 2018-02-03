import sys
import argparse
import subprocess
import signal
import os
import re


def generate_command(openvpn_conf):
    if not os.path.isfile(openvpn_conf):
        raise Exception('openvpn conf is not a file')

    parts = ['/usr/bin/env', 'openvpn']
    with open(openvpn_conf) as f:
        lines = f.read().strip().split(os.linesep)
        for line in lines:
            if not re.match('^\s*#', line):
                opts = ('--' + re.sub('\s*#.*$', '', line)).split(' ')
                parts.extend(opts)
    return parts


def run_command(openvpn_conf):
    if not os.path.isfile(openvpn_conf):
        raise Exception('openvpn conf is not a file')

    openvpn_dir = os.path.dirname(openvpn_conf)
    parts = generate_command(openvpn_conf)
    os.chdir(openvpn_dir)
    p = subprocess.Popen(
        parts,
        stdout=sys.stdout,
        stderr=sys.stderr,
        close_fds=True,
    )
    return p


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--dir', required=True)
    args.add_argument('--config', required=True)
    args.add_argument('--connect', action='store_true', required=False)
    args = args.parse_args()

    if not args.dir.startswith('/'):
        args.dir = os.path.join(os.getcwd(), args.dir)

    if not os.path.isdir(args.dir):
        print('--dir is not a directory')
        sys.exit(1)

    args.config = os.path.join(args.dir, '.'.join([args.config, 'conf']))

    if not os.path.isfile(args.config):
        print('--config is not a file')
        sys.exit(1)

    if not args.connect:
        parts = generate_command(args.config)
        print(' '.join(parts))

    else:
        p = run_command(args.config)

        def shutdown(*args):
            print('***** CTRL-C detected! Shutting down OpenVPN... *****\n')
            p.terminate()

        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)

        p.wait()

if '__main__' == __name__:
    main()
