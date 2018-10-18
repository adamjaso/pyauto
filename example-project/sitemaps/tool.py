import os
import re
import sys
import csv
import six
import gzip
import shutil
import argparse
import requests
from collections import OrderedDict
from reppy.robots import Robots
from pyauto.util import yamlutil
from . import parser

if six.PY2:
    import urlparse as parse
else:
    from urllib import parse


def main():
    args = argparse.ArgumentParser()
    args.add_argument('name')
    parsers = args.add_subparsers(dest='action')
    robots = parsers.add_parser('read-robots')
    robots.add_argument('url')
    sitemaps = parsers.add_parser('read-sitemaps')
    sitemaps.add_argument('url')
    sitemaps.add_argument('outdir', type=os.path.abspath)
    sitemaps.add_argument('outfile', type=os.path.abspath)
    sort = parsers.add_parser('sort-sitemaps')
    sort.add_argument('outfile', type=os.path.abspath)
    sort.add_argument('--downloads', type=os.path.abspath, required=True)
    sort.add_argument('--urlsets', type=os.path.abspath, required=True)
    sort.add_argument('--sitemaps', type=os.path.abspath, required=True)
    test_gz = parsers.add_parser('test-gzip')
    test_gz.add_argument('filename')
    convert_csv = parsers.add_parser('convert-to-csv')
    convert_csv.add_argument('directory', type=os.path.abspath)
    convert_csv.add_argument('-k', '--keep', action='store_true')
    dl_sitemaps = parsers.add_parser('download-sitemaps')
    dl_sitemaps.add_argument('sitemapsdirectory', type=os.path.abspath)
    dl_sitemaps.add_argument('outdir', type=os.path.abspath)

    args = args.parse_args()

    if 'read-robots' == args.action:
        read_robots(args)

    elif 'read-sitemaps' == args.action:
        read_sitemaps(args)

    elif 'test-gzip' == args.action:
        test_gzip(args)

    elif 'sort-sitemaps' == args.action:
        sort_sitemaps(args)

    elif 'convert-to-csv' == args.action:
        convert_to_csv(args)

    elif 'download-sitemaps' == args.action:
        download_sitemaps(args)


def read_robots(args):
    sitemaps = get_sitemaps(args.url)
    sys.stdout.write(yamlutil.dump_dict({
        args.name: [url for url in sitemaps]
    }))
    sys.stdout.flush()


def read_sitemaps(args):
    filename = os.path.abspath(args.url)
    with open(filename) as f:
        urls = yamlutil.load_dict(f)[args.name]
    sitemap_downloads = []
    for url in urls:
        name = get_url_name(url)
        outfilename = os.path.join(args.outdir, name)
        get_url(url, outfilename)
        sitemap_downloads.append(outfilename)
    with open(args.outfile, 'w') as f:
        f.write(yamlutil.dump_dict({args.name: sitemap_downloads}))


def test_gzip(args):
    if is_gzipped(args.filename):
        sys.exit(0)
    else:
        sys.exit(1)


def sort_sitemaps(args):
    results = OrderedDict([
        (args.name, OrderedDict([
            ('urlsets', []),
            ('sitemaps', [])
        ]))
    ])
    for fn in os.listdir(args.downloads):
        fn = os.path.join(args.downloads, fn)
        #if is_gzipped(fn):
        #    raise Exception('file is still gzipped: {0}'.format(fn))
        if parser.detect_doctype(fn, 'sitemapindex'):
            dst = os.path.join(args.sitemaps, os.path.basename(fn))
            results[args.name]['urlsets'].append(dst)
        elif parser.detect_doctype(fn, 'urlset'):
            dst = os.path.join(args.urlsets, os.path.basename(fn))
            results[args.name]['sitemaps'].append(dst)
        else:
            print('file has unknown doctype: {0}'.format(fn))
            continue
        shutil.move(fn, dst)
    with open(args.outfile, 'w') as f:
        f.write(yamlutil.dump_dict(results))


def convert_to_csv(args):
    files = [f for f in os.listdir(args.directory)]
    for fn in files:
        fn = os.path.join(args.directory, fn)
        if os.path.isdir(fn):
            continue
        elif fn.endswith('.csv'):
            continue
        dst = '.'.join([fn, 'csv'])
        print('converting', fn, '...')
        with open(dst, 'w') as f:
            try:
                parser.parse_xml_file_to_csv_stream(fn, f)
            except Exception as e:
                print(e)
        if not args.keep:
            os.remove(fn)


def download_sitemaps(args):
    for fn in os.listdir(args.sitemapsdirectory):
        fn = os.path.join(args.sitemapsdirectory, fn)
        if os.path.isdir(fn):
            continue
        with open(fn) as f:
            reader = csv.DictReader(f)
            for url in reader:
                name = get_url_name(url['loc'])
                dst = os.path.join(args.outdir, name)
                if 'loc' not in url or not url['loc']:
                    continue
                print('getting', url['loc'], '...')
                if not os.path.isfile(dst):
                    get_url(url['loc'], dst)


def get_url(url, filename):
    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=5)
    s.mount('http://', a)
    s.mount('https://', a)
    with s.get(url, stream=True, allow_redirects=True, timeout=(60.0, 120.0)) as res:
        if int(res.status_code) // 100 != 2:
            print('got error ', res.status_code, 'for', url)
            return
        with open(filename, 'wb') as f:
            shutil.copyfileobj(res.raw, f)


def get_sitemaps(url):
    robots = Robots.fetch(url)
    for sitemap in robots.sitemaps:
        yield sitemap


def get_url_name(url):
    parts = parse.urlparse(url)
    sanitize = '[^a-zA-Z0-9_.-]+'
    return '__'.join([
        re.sub('[^a-zA-Z0-9_.-]+', '__', parts.path),
        re.sub('[^a-zA-Z0-9_.-]+', '__', parts.query)]).strip('_')


def is_gzipped(filename):
    try:
        with gzip.open(filename, 'r') as f:
            f.read()
        return True
    except IOError:
        return False


if '__main__' == __name__:
    main()
