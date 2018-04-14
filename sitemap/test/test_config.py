import os
import six
import responses
from six import StringIO
from unittest import TestCase
from pyauto.core import deploy, config as core_config
from pyauto.csvdb import db, config as csvdb_config
from pyauto.sitemap import config as sitemap_config
from pyauto.filecache import config as filecache_config
from collections import OrderedDict

core_config.set_id_key('id')
dirname = os.path.dirname(os.path.abspath(__file__))
example_db = os.path.join(dirname, 'sitemaps.db')
sitemapindex_file = os.path.join(dirname, 'sitemapindex.xml')
conf = deploy.Command(os.path.join(dirname, 'config.yml'), [])\
    .config
local = conf.local
csvdb = conf.csvdb
sitemap = conf.sitemap

example_url = 'https://jobs.washingtonpost.com/sitemapindex.xml'
example_sitemap_url = OrderedDict([
    ('id', 'archive'),
    ('type', 'sitemapindex'),
    ('url', example_url),
])
example_site = OrderedDict([
    ('id', 'jobs.washingtonpost.com'),
    ('urls', [example_sitemap_url])
])
example_site_added = OrderedDict([
    ('id', 'jobs1.washingtonpost.com'),
    ('urls', [example_sitemap_url])
])

threebee_urlset_csv = os.path.join(dirname, 'cache/3b/7e/ac/3b7eac2af1bb0069da33dc9d99a899e741e5f2f1489af4536d4f37a1a602270d.urlset.csv')
threebee_csv = os.path.join(dirname, 'cache/3b/7e/ac/3b7eac2af1bb0069da33dc9d99a899e741e5f2f1489af4536d4f37a1a602270d.csv')
threebee = os.path.join(dirname, 'cache/3b/7e/ac/3b7eac2af1bb0069da33dc9d99a899e741e5f2f1489af4536d4f37a1a602270d')



def respond_sitemapindex():
    responses.add(responses.GET, example_url, body=open(sitemapindex_file, 'r').read())


def setUpModule():
    sitemap.append_site(example_site_added)


def tearDownModule():
    if os.path.isfile(example_db):
        os.remove(example_db)


class Sitemap(TestCase):
    def test_append_site(self):
        self.assertEqual(len(sitemap.sites), 2)

    def test_get_site(self):
        site = sitemap.get_site('jobs1.washingtonpost.com')
        self.assertIsInstance(site, sitemap_config.Site)

    def test_get_site_path_csv(self):
        site_path_csv = conf.get_resource(
            'sitemap/get_site_path_csv,jobs1.washingtonpost.com,archive')
        self.assertEqual(site_path_csv, threebee_csv)

    def test_get_site_path_urlset_csv(self):
        site_path_urlset_csv = conf.get_resource(
            'sitemap/get_site_path_urlset_csv,jobs1.washingtonpost.com,archive')
        self.assertEqual(site_path_urlset_csv, threebee_urlset_csv)


class Site(TestCase):
    def setUp(self):
        self.site = sitemap.get_site('jobs1.washingtonpost.com')

    def test_append_url(self):
        self.assertEqual(len(self.site.urls), 1)
        self.site.append_url(example_sitemap_url)
        self.assertEqual(len(self.site.urls), 2)

    def test_get_url(self):
        url = self.site.get_url('archive')
        self.assertIsInstance(url, sitemap_config.SitemapURL)

    @responses.activate
    def test_calculate_size(self):
        for url in self.site.urls:
            respond_sitemapindex()
            url.get_url()
        size = self.site.calculate_size()


class SitemapURL(TestCase):
    def setUp(self):
        self.url = sitemap\
            .get_site('jobs1.washingtonpost.com')\
            .get_url('archive')

    def test_sourcefile(self):
        self.assertEqual(self.url.sourcefile, threebee)

    def test_source_doctype(self):
        self.assertEqual(self.url.source_doctype, 'sitemapindex')

    def test_csvfile(self):
        self.assertEqual(self.url.csvfile, threebee_csv)

    def test_urlset_csvfile(self):
        self.assertEqual(self.url.urlset_csvfile, threebee_urlset_csv)

    def test_get_cache_entry(self):
        self.assertIsInstance(
            self.url.get_cache_entry(), filecache_config.CacheEntry)

#    def test_calculate_size(self):
#        pass

    def test_get_url(self):
        self.assertEqual(self.url.get_url(), threebee)

#    def test_get_urlset_urls(self):
#        print(self.url.get_urlset_urls())
#        pass

#    def test_calculate_urlset_size(self):
#        pass

    def test_parse_xml_file_to_csv_stream(self):
        output = StringIO()
        self.url.parse_xml_file_to_csv_stream(output)
        with open(threebee_csv) as f:
            self.assertEqual(f.read().strip(), output.getvalue().strip())

    def test_parse_xml_file_to_csv_file(self):
        if os.path.isfile(threebee_csv):
            os.remove(threebee_csv)
        self.url.parse_xml_file_to_csv_file()
        self.assertTrue(os.path.isfile(threebee_csv))

    def test_parse_urlset_xml_file_to_csv_stream(self):
        expected = """
loc,lastmod
https://jobs.washingtonpost.com/sitemap1-101.xml,2018-03-26T20:14:32+00:00
https://jobs.washingtonpost.com/sitemap1-105.xml,2018-03-26T20:14:32+00:00
https://jobs.washingtonpost.com/sitemap1-100.xml,2018-03-26T20:14:32+00:00
https://jobs.washingtonpost.com/sitemap1-DynamicTerms.xml,2018-03-26T20:14:32+00:00
https://jobs.washingtonpost.com/sitemap2-1.xml,2018-03-26T20:14:32+00:00
https://jobs.washingtonpost.com/sitemap3-1.xml,2018-03-26T20:14:32+00:00
https://jobs.washingtonpost.com/sitemap4-1.xml,2018-03-26T20:14:32+00:00
https://jobs.washingtonpost.com/sitemap5.xml,2018-03-26T20:14:32+00:00
https://jobs.washingtonpost.com/sitemap7.xml,2018-03-26T20:14:32+00:00
"""
        output = StringIO()
        self.url.parse_xml_file_to_csv_stream(output)
        self.assertEqual(output.getvalue().strip(), expected.strip())

    def test_parse_urlset_xml_file_to_csv_file(self):
        filename = self.url.urlset_csvfile
        self.assertFalse(os.path.isfile(filename))
        filename = self.url.parse_xml_file_to_csv_file()
        self.assertTrue(os.path.isfile(filename))


class SitemapEntry(TestCase):
#    def test_calculate_size(self):
#        pass

    def setUp(self):
        self.url = sitemap\
            .get_site('jobs1.washingtonpost.com')\
            .get_url('archive')

    def test_get_url(self):
        pass

    def test_get_cache_filename(self):
        pass

    def test_parse_urlset(self):
        pass
