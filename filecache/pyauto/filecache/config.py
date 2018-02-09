from __future__ import print_function
import os
import sys
import six
import json
import gzip
import time
import errno
import shutil
import zipfile
import requests
from hashlib import sha256
from binascii import hexlify
from pyauto.core import config
from collections import defaultdict
from pyauto.util import uriutil as uri
from pyauto.local import config as local_config
from pyauto.util.strutil import get_dir_size, get_file_size


def remove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise


def makedirs(dirname):
    try:
        os.makedirs(dirname)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


class FileCache(config.Config):
    def __init__(self, config, parent=None):
        super(FileCache, self).__init__(config, parent)
        self['key_data'] = [KeyData(e, self) for e in self.get('key_data', [])]

    def make_cache_key(self, cache_key_data):
        cache_key_data = json.dumps(cache_key_data)
        print
        if six.PY3:
            cache_key_data = cache_key_data.encode('utf-8')
        cache_key = hexlify(sha256(cache_key_data).digest())
        if six.PY3:
            cache_key = cache_key.decode('utf-8')
        return cache_key

    def get_cache_path(self, cache_key_data, ext=None):
        cache_key = self.make_cache_key(cache_key_data)
        cache_path = self.config.local.get_workspace_path(
                self.directory, cache_key[0:2], cache_key[2:4], cache_key[4:6], cache_key)
        cache_dir = os.path.dirname(cache_path)
        makedirs(cache_dir)
        if ext is not None:
            cache_key = '.'.join([cache_key, ext])
        return os.path.join(cache_dir, cache_key)

    def get_cache_entry(self, cache_key_data):
        return CacheEntry(self, cache_key_data)

    def get_key_data(self, id):
        for key_data in self.key_data:
            if key_data.get_id() == id:
                return key_data
        raise Exception('unknown filecache entry: {0}'.format(id))

    def get_key_data_path(self, id, attr, *args):
        keyd = self.get_key_data(id)
        path = getattr(keyd.entry, attr)
        if len(args) > 0:
            return path(*args)
        return path


class KeyData(config.Config):
    def __init__(self, config, parent=None):
        super(KeyData, self).__init__(config, parent)
        self['entry'] = CacheEntry(parent, self.data)


class CacheEntry(object):
    _file_attrs = [
        'file',
        'meta_file',
        'gunzipped_file',
        'extract_dirname']

    def __init__(self, filecache, cache_key_data):
        self.config = filecache
        self.cache_key_data = cache_key_data
        if cache_key_data is None:
            raise Exception('invalid cache key data: None')
        try:
            json.dumps(cache_key_data)
        except:
            raise Exception('invalid cache key data: Not JSON serializable')

    def calculate_size(self):
        sizes = defaultdict(dict)
        sizes['total']['name'] = self.cache_key_data
        sizes['total']['count'] = 0
        sizes['total']['size'] = 0
        for attr in self._file_attrs:
            fn = getattr(self, attr)
            fs = get_file_size(fn)
            if fs is None:
                continue
            sizes['total']['count'] += fs['count']
            sizes['total']['size'] += fs['size']
            sizes['files'][attr] = fs
        return sizes

    @property
    def exists(self):
        return os.path.isfile(self.file)

    def save(self, stream, bytes_total=None, **user_data):
        bytes_total = int(bytes_total or 0)

        def print_progress(bytes_read):
            if bytes_total > 0:
                bytes_percent = float(
                        int(bytes_read * 1000 / bytes_total)) / 10.0
                sys.stderr.write((' ' * 32) + '\r' +
                        str(bytes_read) + 'b / ' + str(bytes_total) +
                        'b | ' + str(bytes_percent) + ' %')

        with open(self.file, 'wb') as f:
            bytes_read = 0
            for chunk in stream:
                bytes_read += len(chunk)
                f.write(chunk)
                print_progress(bytes_read)
        print()

        self.save_meta(**user_data)
        return self


    def save_meta(self, **kwargs):
        if os.path.isfile(self.meta_file):
            meta = self.load_meta()
        else:
            meta = {
                'time_created': int(time.time()),
                'cache_key_data': self.cache_key_data,
                'user_data': {}
            }
        meta['time_accessed'] = int(time.time())
        meta['user_data'].update(kwargs)

        with open(self.meta_file, 'w') as f:
            json.dump(meta, f, indent=2)
        return self

    def load_meta(self):
        with open(self.meta_file) as f:
            return json.load(f)

    def get_user_data(self):
        if not os.path.isfile(self.meta_file):
            return {}
        meta = self.load_meta()
        return meta['user_data']

    def is_expired(self, ttl):
        if not os.path.isfile(self.meta_file):
            return True
        meta = self.load_meta()
        return int(time.time()) - meta['time_created'] > ttl

    def is_recently_used(self, ttl):
        if not os.path.isfile(self.meta_file):
            return False
        meta = self.load_meta()
        return int(time.time()) - meta['time_accessed'] <= ttl

    @property
    def file(self):
        return self.config.get_cache_path(self.cache_key_data)

    @property
    def gunzipped_file(self):
        return self.config.get_cache_path(self.cache_key_data, 'gunzipped')

    @property
    def extract_dirname(self):
        return self.config.get_cache_path(
                self.cache_key_data, 'extracted')

    @property
    def extract_dir(self):
        extract_dir = self.extract_dirname
        makedirs(extract_dir)
        return extract_dir

    @property
    def meta_file(self):
        return self.config.get_cache_path(self.cache_key_data, 'json')

    def extracted_path(self, *filename):
        return os.path.join(self.extract_dir, *filename)

    def zip_extract(self):
        extract_dir = self.extract_dir
        with zipfile.ZipFile(self.file) as zf:
            zf.extractall(extract_dir)
        return extract_dir

    def gzip_decompress(self):
        filei = self.file
        fileo = self.gunzipped_file
        with gzip.open(filei, 'rb') as fi, open(fileo, 'wb') as fo:
            shutil.copyfileobj(fi, fo)
        return fileo

    def get_url(self):
        if not self.exists:
            with requests.get(
                    self.cache_key_data, stream=True,
                    headers=self.config.get('http_headers', {})) as r:
                r.raise_for_status()
                cl = r.headers.get('content-length', 0)
                self.save(r, bytes_total=cl)
        return self.file

    def remove(self):
        ifile = self.file
        if os.path.isfile(ifile):
            remove(ifile)

        mfile = self.meta_file
        if os.path.isfile(mfile):
            remove(mfile)

        gzfile = self.gunzipped_file
        if os.path.isfile(gzfile):
            remove(gzfile)

        exdir = self.extract_dir
        if os.path.isdir(exdir):
            shutil.rmtree(exdir)


config.set_config_class('filecache', FileCache)
