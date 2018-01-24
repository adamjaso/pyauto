from __future__ import print_function
import os
import json
from pyauto.core import config
from pyauto.local import config as local_config
from . import config as ouidb_config
from . import server


def get_source_file(config):
    return config.ouidb.get_source_file()


def get_dest_file(config):
    return config.ouidb.get_dest_file()


def get_db(config):
    return config.ouidb.get_db()


def create_db(config):
    return config.ouidb.create_db()


def download_source(config, force=None):
    return config.ouidb.download_source(force)


def parse_source_file(config):
    for entry in config.ouidb.parse_source():
        print(json.dumps(entry, indent=2))


def import_db(config, force=None):
    if not os.path.isfile(config.ouidb.get_dest_file()) or force:
        config.ouidb.import_db()
    return config.ouidb.get_dest_file()


def get_top_entries(config):
    result = config.ouidb.get_top_entries()
    return json.dumps(result, indent=2)


def find_prefix(config, prefix):
    result = config.ouidb.find_prefix(prefix)
    return json.dumps(result, indent=2)


def start_server(config):
    server.init_config(config.ouidb)
    server.app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))


if '__main__' == __name__:
    from pyauto.core import deploy
    deploy.main()
