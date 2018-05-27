import os
from unittest import TestCase
from pyauto.util import ziputil

samples_dirname = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'samples')
ignore_filename = os.path.join(samples_dirname, '.ignorefile')
samples_filename = os.path.join(samples_dirname, 'gzsample.txt')
zip_filename = ''.join([samples_dirname, '.zip'])


class Ziputil(TestCase):
    def tearDown(self):
        if os.path.isfile(zip_filename):
            os.remove(zip_filename)

    def test_zip_dir(self):
        filename = ziputil.zip_dir(samples_dirname, zip_filename)
        self.assertTrue(os.path.isfile(filename))

    def test_list_files(self):
        files = ziputil.list_files(samples_dirname)
        self.assertListEqual(files, [
            {'sha1': '8ffd17e00b71cd3fbda5c8935da5153d07dd0236',
             'fn': 'gzsample.txt',
             'size': 20001},
            {'sha1': '17cc46a08a8cb768fb410c3e42de06d48dc2fecb',
             'fn': '.ignorefile',
             'size': 13}])
        files = ziputil.list_files(samples_dirname, ignore_filename)
        self.assertListEqual(files, [])


    def test_file_sha1(self):
        sha1 = ziputil.file_sha1(samples_filename)
        self.assertEqual(sha1, '8ffd17e00b71cd3fbda5c8935da5153d07dd0236')

    def test_file_size(self):
        size = ziputil.file_size(samples_filename)
        self.assertEqual(size, 20001)

    def test_parse_ignore_file(self):
        ignore = ziputil.parse_ignore_file(ignore_filename)
        self.assertListEqual(ignore, ['gzsample.txt', '.git/', '.gitignore'])
