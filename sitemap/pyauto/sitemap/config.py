from __future__ import print_function
import os
import re
import sys
import csv
import json
import shutil
import requests
from lxml import etree
from collections import OrderedDict, defaultdict
from pyauto.core import config
from pyauto.util.strutil import get_file_size
from . import parser


class Sitemap(config.Config):
    def __init__(self, config, parent=None):
        super(Sitemap, self).__init__(config, parent)
        self['sites'] = [Site(s, self) for s in self['sites']]

    def append_site(self, site):
        site = Site(site, self)
        self['sites'].append(site)
        return self

    def get_site(self, id):
        for site in self.sites:
            if site.get_id() == id:
                return site
        raise Exception('unknown site: {0}'.format(id))

    def get_site_path_csv(self, site_id, url_id):
        return self.get_site(site_id).get_url(url_id).csvfile

    def get_site_path_urlset_csv(self, site_id, url_id):
        return self.get_site(site_id).get_url(url_id).urlset_csvfile


class Site(config.Config):
    def __init__(self, config, parent=None):
        super(Site, self).__init__(config, parent)
        self['urls'] = [SitemapURL(u, self) for u in self['urls']]

    def append_url(self, url):
        url = SitemapURL(url, self)
        self['urls'].append(url)
        return self

    def get_url(self, id):
        for url in self.urls:
            if url.get_id() == id:
                return url
        raise Exception('unknown url: {0}'.format(id))

    def calculate_size(self):
        size = defaultdict(dict)
        size['total']['size'] = 0
        size['total']['count'] = 0
        size['files'] = []

        for url in self.urls:
            s = url.calculate_size()
            size['total']['size'] += s['total']['size']
            size['total']['count'] += s['total']['count']
            size['files'].extend(s['files'])

        return size


class SitemapURL(config.Config):
    def __init__(self, config, parent=None):
        super(SitemapURL, self).__init__(config, parent)

    @property
    def sourcefile(self):
        ce = self.get_cache_entry()
        fn = ce.file
        if self.url.endswith('.gz'):
            fn = ce.gunzipped_file
        return fn

    @property
    def source_doctype(self):
        return parser.get_file_doctype(self.sourcefile)

    @property
    def csvfile(self):
        ce = self.get_cache_entry()
        fn = ce.file
        if self.url.endswith('.gz'):
            fn = ce.gunzipped_file
        return '.'.join([fn, 'csv'])

    @property
    def urlset_csvfile(self):
        ce = self.get_cache_entry()
        fn = ce.file
        if self.url.endswith('.gz'):
            fn = ce.gunzipped_file
        return '.'.join([fn, 'urlset', 'csv'])

    def get_cache_entry(self):
        return self.config.config.config.filecache.get_cache_entry(self.url)

    def get_files(self):
        ce = self.get_cache_entry()
        files = []
        if not ce.exists:
            return files
        files.extend(list(ce.get_files()))
        files.append(self.csvfile)
        files.append(self.urlset_csvfile)
        return files

    def calculate_size(self):
        ce = self.get_cache_entry()
        size = defaultdict(dict)
        size['total']['size'] = 0
        size['total']['count'] = 0
        size['files'] = []

        if not ce.exists:
            return size
        ce_size = ce.calculate_size()
        size['total']['size'] += ce_size['total']['size']
        size['total']['count'] += ce_size['total']['count']
        size['files'].extend([
            f['name'] for f in ce_size['files'].values()])

        csv_size = get_file_size(self.csvfile)
        if csv_size is not None:
            size['total']['size'] += csv_size['size']
            size['total']['count'] += csv_size['count']
            size['files'].append(self.csvfile)

        sec_csv_size = get_file_size(self.urlset_csvfile)
        if sec_csv_size is not None:
            size['total']['size'] += sec_csv_size['size']
            size['total']['count'] += sec_csv_size['count']
            size['files'].append(self.urlset_csvfile)

        self.calculate_urlset_size(size)

        return size

    def get_url(self):
        entry = self.get_cache_entry()
        entry.get_url()
        if self.get('gzip'):
            return entry.gzip_decompress()
        return entry.file

    def get_urlset_urls(self):
        if parser.detect_doctype(self.sourcefile, 'urlset'):
            return
        entry = self.get_cache_entry()
        fc = self.config.config.config.filecache
        with open(self.csvfile) as f:
            reader = csv.DictReader(f)
            for row in reader:
                sme = SitemapEntry(row, self)
                try:
                    sme.get_url()
                except Exception as e:
                    logerr(e)

    def calculate_urlset_size(self, sizes):
        if parser.detect_doctype(self.sourcefile, 'urlset'):
            return None
        if not os.path.isfile(self.csvfile):
            return None
        entry = self.get_cache_entry()
        if not entry.exists:
            return None
        fc = self.config.config.config.filecache
        with open(self.csvfile) as f:
            reader = csv.DictReader(f)
            for row in reader:
                sme = SitemapEntry(row, self)
                size = sme.calculate_size()
                sizes['total']['size'] += size['total']['size']
                sizes['total']['count'] += size['total']['count']
                sizes['files'].extend([
                    f['name'] for f in size['files'].values()])

    def parse_xml_file_to_csv_stream(self, outstream):
        parser.parse_xml_file_to_csv_stream(self.sourcefile, outstream)

    def parse_xml_file_to_csv_file(self):
        csvfile = self.csvfile
        with open(csvfile, 'w') as f:
            self.parse_xml_file_to_csv_stream(f)
        return csvfile

    def parse_urlset_xml_file_to_csv_stream(self, outstream):
        if parser.detect_doctype(self.sourcefile, 'urlset'):
            return
        with open(self.csvfile) as f:
            reader = csv.DictReader(f)
            csvout = csv.writer(outstream,
                                lineterminator='\n')
            csvout.writerow(parser.get_urlset_names())
            for row in reader:
                sme = SitemapEntry(row, self)
                sme.parse_urlset(outstream, include_columns=False)
                outstream.flush()

    def parse_urlset_xml_file_to_csv_file(self):
        if parser.detect_doctype(self.sourcefile, 'urlset'):
            return
        with open(self.urlset_csvfile, 'w') as f:
            self.parse_urlset_xml_file_to_csv_stream(f)
        return self.urlset_csvfile


class SitemapEntry(config.Config):
    def __init__(self, config, parent=None):
        super(SitemapEntry, self).__init__(config, parent)
        self.filecache = self.config.config.config.config.filecache
        self.cache_entry = self.filecache.get_cache_entry(self.loc)

    def calculate_size(self):
        return self.cache_entry.calculate_size()

    def get_url(self):
        print('getting', self.loc, '...')
        fn = self.cache_entry.get_url()
        if self.loc.endswith('.gz'):
            fn = self.cache_entry.gzip_decompress()
        print('saved to', fn, '!')
        return fn

    def get_cache_filename(self):
        if self.loc.endswith('.gz'):
            return self.cache_entry.gunzipped_file
        return self.cache_entry.file

    def parse_urlset(self, outstream, **kwargs):
        cache_filename = self.get_cache_filename()
        if os.path.isfile(cache_filename) and \
                parser.detect_doctype(cache_filename, 'urlset'):
            parser.parse_xml_file_to_csv_stream(
                    self.get_cache_filename(), outstream, **kwargs)
        else:
            print('not an urlset')
        print('finished', self.loc)


def logerr(*args):
    sys.stderr.write(' '.join([str(a) for a in args]) + '\n')


config.set_config_class('sitemap', Sitemap)
