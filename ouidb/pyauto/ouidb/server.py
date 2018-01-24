import os
from functools import wraps
from flask import Flask, jsonify, request
from . import api
from . import config as ouidb_config
from pyauto.util import uriutil


config = None
app = Flask(__name__)
#app.debug = True


def init_config(conf):
    global config
    config = conf


def build_uri(path, **query):
    return uriutil.format(
        scheme=request.scheme,
        netloc=str(request.host),
        path=path,
        query=query,
    )


def load_config(func):

    @wraps(func)
    def _wrap(*args, **kwargs):
        global config
        return func(config, *args, **kwargs)

    return _wrap


@app.route('/')
@load_config
def index(config):
    return jsonify({
        'row_count': api.MacVendor(config).count_rows(),
        'countries_uri': build_uri('/countries'),
        'vendors_uri': build_uri('/vendors'),
    })


@app.route('/countries')
@load_config
def countries(config):
    min_count = int(request.args.get('min_count', 0))
    order = request.args.get('order')
    country_count = api.MacVendor(config).count_countries(min_count, order)
    return jsonify({
        'country_count': country_count,
    })


@app.route('/vendors')
@load_config
def vendors(config):
    min_count = int(request.args.get('min_count', 0))
    order = request.args.get('order')
    q = request.args.get('q', '')
    if q:
        vendor_count = api.MacVendor(config).find_vendors_like_name(q, min_count)
    else:
        vendor_count = api.MacVendor(config).count_vendors(min_count, order)
    return jsonify({
        'vendor_count': vendor_count,
    })


@app.route('/vendors/<vendor_name>')
@load_config
def get_vendor(config, vendor_name):
    vendor = api.MacVendor(config).find_vendor_by_name(vendor_name)
    return jsonify(vendor)


@app.route('/vendors/<vendor_name>/prefixes')
@load_config
def get_vendor_prefixes(config, vendor_name):
    prefixes = api.MacVendor(config).find_prefixes_by_vendor_name(vendor_name)
    return jsonify({
        'count': len(prefixes),
        'prefixes': prefixes,
    })


@app.route('/countries/<country>')
@load_config
def get_country(config, country):
    country = api.MacVendor(config).find_country_by_name(country)
    return jsonify(country)


@app.route('/countries//prefixes')
@app.route('/countries/<country>/prefixes')
@load_config
def get_country_prefixes(config, country=None):
    country = country or ''
    prefixes = api.MacVendor(config).find_prefixes_by_country(country)
    return jsonify({
        'count': len(prefixes),
        'prefixes': prefixes,
    })


@app.route('/prefixes/<prefix>')
@load_config
def get_prefix(config, prefix):
    prefixes = api.MacVendor(config).find_prefix(prefix)
    return jsonify(prefixes)


@app.route('/prefixes')
@load_config
def get_prefixes(config):
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    prefixes = api.MacVendor(config).find_prefixes(page, limit)
    return jsonify({
        'count': len(prefixes),
        'prefixes': prefixes,
    })
