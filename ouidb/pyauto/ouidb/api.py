import re
import sqlite3
from collections import OrderedDict


class MacVendor(object):
    def __init__(self, config):
        self.config = config
        self.db = config.get_db()

    def count_rows(self):
        res = self.db.execute('select count(*) count from mac_vendor')
        row = res.fetchone()
        res.close()
        return int(row['count'])

    def count_countries(self, min_count=0, order=None):
        if order not in ['country', 'count']:
            order = 'country'
        res = self.db.execute(
            'select country, count(*) count from mac_vendor '
            'group by country having count > ? order by {0}'
            .format(order), (min_count,))
        countries = OrderedDict([
            (row['country'], row['count'])
            for row in res.fetchall()])
        res.close()
        return countries

    def count_vendors(self, min_count=0, order=None):
        if order not in ['vendor_name', 'count']:
            order = 'vendor_name'
        res = self.db.execute(
            'select vendor_name, count(*) count from mac_vendor '
            'group by vendor_name having count > ? order by {0}'
            .format(order), (min_count,))
        vendors = OrderedDict([
            (row['vendor_name'], row['count'])
            for row in res.fetchall()])
        res.close()
        return vendors

    def find_prefixes_by_vendor_name(self, name):
        res = self.db.execute(
            'select mac_prefix, vendor_address, country from mac_vendor '
            'where vendor_name = ?', (name,))
        prefixes = [row for row in res.fetchall()]
        res.close()
        return prefixes

    def find_vendor_by_name(self, name):
        res = self.db.execute(
            'select vendor_address, vendor_name, country, count(*) prefix_count '
            'from mac_vendor '
            'where vendor_name = ? group by vendor_name', (name,))
        vendor = [row for row in res.fetchall()]
        res.close()
        return vendor[0] if len(vendor) > 0 else None

    def find_prefixes_by_country(self, name):
        res = self.db.execute(
            'select vendor_address, vendor_name, count(*) prefix_count '
            'from mac_vendor '
            'where country = ? group by vendor_name', (name,))
        vendors = [row for row in res.fetchall()]
        res.close()
        return vendors

    def find_country_by_name(self, name):
        res = self.db.execute(
            'select country, count(*) prefix_count '
            'from mac_vendor '
            'where country = ? group by country', (name,))
        country = [row for row in res.fetchall()]
        res.close()
        return country[0] if len(country) > 0 else None

    def find_vendors_like_name(self, name, min_count=0):
        res = self.db.execute(
            'select vendor_name, count(*) count from mac_vendor '
            'where vendor_name like ? group by vendor_name having count > ?',
            ('%' + name + '%', min_count))
        vendors = OrderedDict([
            (row['vendor_name'], row['count'])
            for row in res.fetchall()])
        res.close()
        return vendors

    def find_prefix(self, prefix):
        prefix = re.sub('[^a-fA-F0-9]', '', prefix)
        res = self.db.execute(
            'select * from mac_vendor '
            'where mac_prefix = ?', (prefix,))
        prefixes = res.fetchone()
        res.close()
        return prefixes

    def find_prefixes(self, page=1, limit=100):
        page = max(page, 0)
        limit = min(max(limit, 0), 100)
        offset = int((page - 1) * limit)
        res = self.db.execute(
            'select * from mac_vendor '
            'limit ?, ?', (offset, limit))
        prefixes = [row for row in res.fetchall()]
        res.close()
        return prefixes
