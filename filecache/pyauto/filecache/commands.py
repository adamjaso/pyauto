from __future__ import print_function
import os
import json
import requests
from pyauto import config
from . import config as filecache_config
from ..local import config as local_config
from ..local import commands as local_commands


list_types = (list, set, tuple)


def get_file(config, data):
    return config.filecache.get_cache_entry(data).file

def get_file_size(config, data):
    size = config.filecache.get_cache_entry(data).calculate_size()
    return json.dumps(size, indent=2)

def get_url(config, url):
    return config.filecache.get_cache_entry(url).get_url()


def remove(config, data):
    return config.filecache.get_cache_entry(data).remove()


def zip_extract(config, data):
    return config.filecache.get_cache_entry(data).zip_extract()


def zip_extract_file(config, data, filepath):
    return config.filecache.get_cache_entry(data).extracted_path(filepath)


def gzip_decompress(config, data):
    return config.filecache.get_cache_entry(data).gzip_decompress()


def key_data_get_file(config, key_data_id):
    return config.filecache.get_key_data(key_data_id).entry.file


def key_data_get_url(config, key_data_id):
    return config.filecache.get_key_data(key_data_id).entry.get_url()


def key_data_remove(config, key_data_id):
    return config.filecache.get_key_data(key_data_id).entry.remove()


def key_data_zip_extract(config, key_data_id):
    return config.filecache.get_key_data(key_data_id).entry.zip_extract()


def key_data_zip_extract_file(config, key_data_id, filepath):
    return config.filecache.get_key_data(key_data_id).entry.extracted_path(filepath)


def key_data_gzip_decompress(config, key_data_id):
    return config.filecache.get_key_data(key_data_id).entry.gzip_decompress()


if '__main__' == __name__:
    from pyauto import deploy
    deploy.main()
