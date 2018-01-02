from collections import OrderedDict
try:
    import urlparse
    import urllib
except ImportError:
    import urllib.parse as urlparse
    import urllib.parse as urllib


def parse(uri):
    parts = urlparse.urlsplit(uri)
    return dict(
        scheme=parts.scheme,
        netloc=parts.netloc,
        path=parts.path,
        query=OrderedDict(urlparse.parse_qsl(parts.query, True)),
        frag=parts.fragment,
    )


def format(**kwargs):
    return urlparse.urlunparse((
        kwargs.get('scheme'),
        kwargs.get('netloc'),
        kwargs.get('path'),
        None,
        format_query(kwargs.get('query', {})),
        kwargs.get('frag'),
    ))


def format_query(*qargs, **query):
    if len(qargs) > 0:
        query = qargs[0]
    return urllib.urlencode(query, True)
