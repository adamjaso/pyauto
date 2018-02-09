import os
import shutil
from unittest import TestCase
from pyauto.core import deploy, config
from pyauto.local import config as local_config
from pyauto.filecache import config as filecache_config
config.set_id_key('id')
dirname = os.path.dirname(os.path.abspath(__file__))
conf = deploy.Command(os.path.join(dirname, 'config.yml'), []).config
local = conf.local
filecache = conf.filecache


cache_key_data = 'abc'
cache_key = '6cc43f858fbb763301637b5af970e2a46b46f461f27e5a0f41e009c59b827b25'
cache_key_path = '6c/c4/3f/{0}'.format(cache_key)
cache_key_path_json = '6c/c4/3f/{0}.json'.format(cache_key)
cache_key_path_extracted = '6c/c4/3f/{0}.extracted'.format(cache_key)
cache_key_path_gunzipped = '6c/c4/3f/{0}.gunzipped'.format(cache_key)
cache_key_path_gunzipped_csv = '6c/c4/3f/{0}.gunzipped.csv'.format(cache_key)


class FileCache(TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_init(self):
        for kd in filecache.key_data:
            self.assertIsInstance(kd, filecache_config.KeyData)

    def test_make_cache_key(self):
        key = filecache.make_cache_key(cache_key_data)
        self.assertEqual(cache_key, key)

    def test_get_cache_path(self):
        path = filecache.get_cache_path(cache_key_data)
        self.assertTrue(path.endswith(cache_key_path))
        self.assertTrue(os.path.isdir(os.path.dirname(path)))

    def test_get_cache_entry(self):
        entry = filecache.get_cache_entry(cache_key_data)
        self.assertIsInstance(entry, filecache_config.CacheEntry)

    def test_get_key_data(self):
        kd = filecache.get_key_data(cache_key_data)
        self.assertIsInstance(kd, filecache_config.KeyData)

    def test_get_key_data_path(self):
        test_results = {
            'file': os.path.join(dirname, 'workspace/cache', cache_key_path),
            'meta_file': os.path.join(dirname, 'workspace/cache', cache_key_path_json),
            'gunzipped_file': os.path.join(dirname, 'workspace/cache', cache_key_path_gunzipped),
            'extract_dirname': os.path.join(dirname, 'workspace/cache', cache_key_path_extracted),
        }
        for attr, expected_path in test_results.items():
            path = filecache.get_key_data_path('abc', attr)
            self.assertEqual(expected_path, path)


class CacheEntry(TestCase):
    def tearDown(self):
        filecache.get_cache_entry('abc').remove()
        ce = filecache.get_cache_entry('edcba')
        if os.path.isdir(ce.extract_dirname):
            shutil.rmtree(ce.extract_dirname)
        ce = filecache.get_cache_entry('abcde')
        if os.path.isfile(ce.gunzipped_file):
            os.remove(ce.gunzipped_file)

    def test_calculate_size(self):
        fn = os.path.join(dirname, 'workspace/cache/cb/23/dd/cb23dd4317a1e244dfffdb37412194357e55aa1efbf2fc1662f5bdfc28e37033')
        fnj = os.path.join(dirname, 'workspace/cache/cb/23/dd/cb23dd4317a1e244dfffdb37412194357e55aa1efbf2fc1662f5bdfc28e37033.json')
        entry = filecache.get_cache_entry('abcde')
        size = entry.calculate_size()
        self.assertDictEqual(size, {
            'total': {
                'name': 'abcde', 'count': 2, 'size': 193},
            'files': {
                'file': {'count': 1, 'size': 63, 'name': fn},
                'meta_file': {'count': 1, 'size': 130, 'name': fnj}
            }
        })

    def test_exists(self):
        entry = filecache.get_cache_entry('abcde')
        self.assertTrue(entry.exists)
        entry = filecache.get_cache_entry('edcba')
        self.assertTrue(entry.exists)

    def test_save(self):
        entry1 = filecache.get_cache_entry('edcba')
        entry2 = filecache.get_cache_entry('abc')
        size = os.stat(entry1.file).st_size
        with open(entry1.file, 'rb') as f:
            entry2.save(f, bytes_total=size)

    def test_load_meta(self):
        entry1 = filecache.get_cache_entry('edcba')
        entry2 = filecache.get_cache_entry('abc')
        size = os.stat(entry1.file).st_size
        with open(entry1.file, 'rb') as f:
            entry2.save(f, bytes_total=size, abc=123)
        entry1 = filecache.get_cache_entry('edcba')
        entry1.load_meta()

    def test_get_user_data(self):
        entry1 = filecache.get_cache_entry('edcba')
        entry2 = filecache.get_cache_entry('abc')
        size = os.stat(entry1.file).st_size
        with open(entry1.file, 'rb') as f:
            entry2.save(f, bytes_total=size, abc=123)
        data = entry2.get_user_data()
        self.assertDictEqual(data, {'abc': 123})

    def test_zip_extract(self):
        entry = filecache.get_cache_entry('edcba')
        dn = entry.zip_extract()
        expected_dn = os.path.join(dirname, 'workspace/cache/17/75/f6/1775f6d0736a4770d0307ab70cd499e394b271b95114c9dadd6fa12177deab55.extracted')
        self.assertEqual(dn, expected_dn)
        self.assertTrue(os.path.isdir(dn))

    def test_extracted_path(self):
        entry = filecache.get_cache_entry('edcba')
        entry.zip_extract()
        fn = entry.extracted_path('abcde.gz')
        self.assertTrue(os.path.isfile(fn))

    def test_gzip_decompress(self):
        entry = filecache.get_cache_entry('abcde')
        entry.gzip_decompress()
        fn = entry.gunzipped_file
        self.assertTrue(os.path.isfile(fn))

