from lxml import etree
import csv


def get_sitemapindex_names():
    return [
        'loc',
        'lastmod']


def get_urlset_names():
    return [
        'loc',
        'lastmod',
        'changefreq',
        'priority',
        'image',  # 5
        'title',
        'keywords',
        'publication_date', 
        'language', 
        'publication_name',  # 10
        'video_url',
        'video_duration',
        'video_thumbnail_url',
        'video_title',
        'video_description',  # 15
        'video_publication_date']


def compare_tag(tag, item):
    return tag == etree.QName(item).localname


def get_urlset_row(item):
    row = [''] * 16
    for item in item.getchildren():
        if isinstance(item, etree._Comment):
            continue
        if compare_tag('loc', item):
            row[0] = item.text
        elif compare_tag('lastmod', item):
            row[1] = item.text
        elif compare_tag('changefreq', item):
            row[2] = item.text
        elif compare_tag('priority', item):
            row[3] = item.text
        elif compare_tag('image', item):
            for item in item.getchildren():
                if compare_tag('loc', item):
                    row[4] = item.text
        elif compare_tag('news', item):
            for item in item.getchildren():
                if compare_tag('title', item):
                    row[5] = item.text
                elif compare_tag('keywords', item):
                    row[6] = item.text
                elif compare_tag('publication_date', item):
                    row[7] = item.text
        elif compare_tag('publication', item):
            for item in item.getchildren():
                if compare_tag('language', item):
                    row[8] = item.text
                elif compare_tag('publication_name', item):
                    row[9] = item.text
        elif compare_tag('video', item):
            for item in item.getchildren():
                if compare_tag('content_loc', item):
                    row[10] = item.text
                elif compare_tag('duration', item):
                    row[11] = item.text
                elif compare_tag('thumbnail_loc', item):
                    row[12] = item.text
                elif compare_tag('title', item):
                    row[13] = item.text
                elif compare_tag('description', item):
                    row[14] = item.text
                elif compare_tag('publication_date', item):
                    row[15] = item.text
    return [(s or '').strip().encode('utf8') for s in row]


def get_sitemapindex_row(item):
    row = [''] * 2
    for item in item.getchildren():
        if compare_tag('loc', item):
            row[0] = item.text.strip()
        elif compare_tag('lastmod', item):
            row[1] = item.text.strip()
    return row


def detect_doctype(filename, doctype):
    try:
        return doctype == get_file_doctype(filename)
    except etree.XMLSyntaxError as e:
        print('failed to detect doctype', filename, str(e))
        return False


def get_file_doctype(filename):
    with open(filename) as f:
        root = etree.parse(f).getroot()
        return get_doctype(root)


def get_doctype(root):
    if compare_tag('urlset', root):
        return 'urlset'
    elif compare_tag('sitemapindex', root):
        return 'sitemapindex'
    else:
        return None


def parse_xml_to_csv(root, include_columns=True):
    doctype = get_doctype(root)
    if doctype is None:
        raise Exception('unparseable xml document; '
                        'root tag not recognized: {0}'
                        .format(etree.QName(root).localname))
    if include_columns:
        columns = None
        if 'urlset' == doctype:
            columns = get_urlset_names()

        elif 'sitemapindex' == doctype:
            columns = get_sitemapindex_names()

        yield columns
    for item in root.getchildren():
        if 'urlset' == doctype:
            yield get_urlset_row(item)
        elif 'sitemapindex' == doctype:
            yield get_sitemapindex_row(item)


def parse_xml_file_to_csv_stream(xmlfilename, outstream, **kwargs):
    with open(xmlfilename) as f:
        csvout = csv.writer(outstream,
                            quoting=csv.QUOTE_MINIMAL,
                            lineterminator='\n')
        root = etree.parse(f).getroot()
        for item in parse_xml_to_csv(root, **kwargs):
            csvout.writerow(item)
