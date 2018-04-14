import os
import sys
import json
import yaml
import shutil
from . import config as sitemap_config
from pyauto.filecache import commands, config as _
from pyauto.csvdb import commands, config as _


def sitemap_get_url(config, site_id, url_id):
    urle = config.sitemap.get_site(site_id).get_url(url_id)
    return urle.get_url()


def sitemap_get_url_size(config, site_id, url_id, include_files=None):
    urle = config.sitemap.get_site(site_id).get_url(url_id)
    size = urle.calculate_size()
    if not include_files:
        del size['files']
    return json.dumps(size)


def sitemap_get_site_size(config, site_id, include_files=None):
    site = config.sitemap.get_site(site_id)
    size = site.calculate_size()
    if not include_files:
        del size['files']
    return json.dumps(size)


def sitemap_to_csv(config, site_id, url_id):
    return config.sitemap.get_site(site_id).get_url(url_id)\
            .parse_xml_file_to_csv_stream(sys.stdout)


def sitemap_to_csv_file(config, site_id, url_id):
    return config.sitemap.get_site(site_id).get_url(url_id)\
                         .parse_xml_file_to_csv_file()


def sitemap_urlset_get_urls(config, site_id, url_id):
    config.sitemap.get_site(site_id).get_url(url_id).get_urlset_urls()


def sitemap_urlset_to_csv(config, site_id, url_id):
    return config.sitemap.get_site(site_id).get_url(url_id)\
                         .parse_urlset_xml_file_to_csv_stream(sys.stdout)


def sitemap_urlset_to_csv_file(config, site_id, url_id):
    return config.sitemap.get_site(site_id).get_url(url_id)\
                         .parse_urlset_xml_file_to_csv_file()


def get_site_path_csv(config, site_id, url_id):
    return config.sitemap.get_site_path_csv(site_id, url_id)


def sitemap_get_doctype(config, site_id, url_id):
    return config.sitemap.get_site(site_id).get_url(url_id).source_doctype


def sitemap_get_doctypes(config, site_id):
    urls = config.sitemap.get_site(site_id).urls
    for url in urls:
        print('\t'.join([url.id, url.source_doctype,]))


def sitemap_parse_robots(config, robots_url):
    robots = sitemap_config.RobotsURL(robots_url, config.filecache)
    robots.get_url()
    robots.get_sitemap_urls()
    return robots.get_sitemap_doctypes()


def sitemap_parse_robots_manifest(config, robots_yaml):
    with open(os.path.abspath(robots_yaml)) as f:
        robots = yaml.load(f)
    yml = sitemap_config.RobotsURL.build_manifest(config.filecache, **{
        prefix: url + '/robots.txt' for prefix, url in robots.items()})
    print(yml)


if '__main__' == __name__:
    from pyauto import deploy
    deploy.main()
