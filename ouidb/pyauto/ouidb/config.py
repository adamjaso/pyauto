import re
import os
import sys
import sqlite3
import requests
from pyauto.core import config
from pyauto.local import config as local_config


ouidb_sql_file = 'ouidb.sql'


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class OUIDB(config.Config):
    def get_source_file(self):
        return self.config.local.get_workspace_path(self.source_file)

    def get_dest_file(self):
        return self.config.local.get_workspace_path(self.dest_file)

    def get_db(self):
        dest_file = self.get_dest_file()
        db = sqlite3.connect(dest_file)
        db.text_factory = str
        db.row_factory = dict_factory
        return db

    def create_db(self):
        db = self.get_db()
        fn = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), ouidb_sql_file)
        with open(fn) as f:
            ouidb_sql = f.read()
        db.execute(ouidb_sql)
        return db

    def get_top_entries(self):
        query = 'select count(vendor_name) count, vendor_name from mac_vendor group by vendor_name having count > 10 order by count;'
        try:
            db = self.get_db()
            results = db.execute(query)
            return [i for i in results]
        finally:
            db.close()

    def find_prefix(self, prefix):
        query = 'select * from mac_vendor where mac_prefix = :prefix'
        try:
            db = self.get_db()
            results = db.execute(query, dict(prefix=prefix))
            return [i for i in results]
        finally:
            db.close()

    def download_source(self, force=None):
        src_url = self.source_url
        src_file = self.get_source_file()
        if os.path.isfile(src_file) and not force:
            return src_file

        try:
            os.makedirs(os.path.dirname(src_file))
        except OSError:
            pass

        res = requests.get(src_url, stream=True)
        res.raise_for_status()
        read_bytes = 0
        bufsize = 16*1024
        total_bytes = int(res.headers.get('Content-Length', 0))
        with open(src_file, 'wb') as f:
            for block in res.iter_content(bufsize):
                f.write(block)
                read_bytes += len(block)
                if total_bytes > 0:
                    percent = str(int(float(read_bytes) /
                                      float(total_bytes) * 1000.0) / 10.0)
                    sys.stderr.write(percent +  '%    \r')
        print('Download complete!')
        return src_file

    def parse_source(self):
        db = self.create_db()
        src_file = self.get_source_file()
        count = 0
        with open(src_file) as f:
            for entry in self.parse_entries(f):
                if count > 0:
                    yield self.parse_entry(entry)
                count += 1

    def import_db(self):
        db = self.get_db()
        query = 'insert into mac_vendor (mac_prefix, vendor_name, vendor_address, country) values (:base16, :org_name, :address, :country)'
        for entry in self.parse_source():
            try:
                db.execute(query, entry)
            except sqlite3.IntegrityError as e:
                if str(e).startswith('UNIQUE'):
                    pass
                else:
                    raise
        db.commit()
        db.close()

    def parse_entries(self, f):
        entry = []
        for line in f:
            if '\n' == line:
                yield entry
                entry = []
            else:
                entry.append(line)
        yield entry

    def parse_entry(self, entry):
        parsed = {
            'post_code': '',
            'address': [],
        }
        line1 = entry[0].split('\t\t')
        line2 = entry[1].split('\t\t')
        parsed['hex'] = re.split('\s+', line1[0].strip())[0]
        parsed['base16'] = re.split('\s+', line2[0].strip())[0]
        parsed['org_name'] = line1[1].strip() if len(line1) > 1 else None
        parsed['address'].append(line2[1].strip())
        line2 = entry[1].split('\t\t')
        for i, line in enumerate(entry[2:]):
            i = i+2
            entry[i] = entry[i].split('\t\t')
            parsed['address'].append(entry[i][-1].strip())
        addr_parts = re.split('\s{2,}', entry[-2][-1].strip())
        if len(addr_parts) > 0:
            parsed['post_code'] = addr_parts[-1]
        parsed['country'] = entry[-1][-1].strip()
        parsed['address'] = '\n'.join(parsed['address'])
        return parsed


config.set_config_class('ouidb', OUIDB)
