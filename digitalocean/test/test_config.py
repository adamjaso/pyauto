import os
import digitalocean as _digitalocean
from unittest import TestCase
from pyauto.core import deploy
from pyauto.digitalocean import config as do_config
dirname = os.path.dirname(os.path.abspath(__file__))
conf = deploy.Command(os.path.join(dirname, 'config.yml'), []).config
local = conf.local
digitalocean = conf.digitalocean


class Digitalocean(TestCase):
    def test_get_droplet(self):
        d = digitalocean.get_droplet('db-sfo1')
        self.assertIsInstance(d, do_config.Droplet)

    def test_get_droplet_profile(self):
        p = digitalocean.get_droplet_profile('default')
        self.assertIsInstance(p, dict)
        self.assertGreater(len(p.keys()), 0)

    def test_get_droplet_client(self):
        c = digitalocean.get_droplet_client()
        self.assertIsInstance(c, _digitalocean.Droplet)

    def test_get_manager_client(self):
        m = digitalocean.get_manager_client()
        self.assertIsInstance(m, _digitalocean.Manager)


class Droplet(TestCase):
    def test_droplet_tag(self):
        d = digitalocean.get_droplet('db-sfo1')
        droplet_tag = ':'.join(['droplet_name', d.droplet_name])
        self.assertEqual(d.droplet_tag, droplet_tag)

    def test_droplet_profile(self):
        d = digitalocean.get_droplet('db-sfo1')
        self.assertIsInstance(d.droplet_profile, dict)

    def test_droplet_name(self):
        d = digitalocean.get_droplet('db-sfo1')
        self.assertEqual(d.droplet_name, 'db-512mb-sfo1')

    def test_get_deploy_opts(self):
        d = digitalocean.get_droplet('db-sfo1')
        options = d.get_deploy_opts(
            user_data='echo hello jdoe > jdoe_greeting.txt')
        self.assertDictEqual(options, {
            'size': '512mb',
            'image': 'ubuntu-16-04-x64',
            'ssh_keys': ['your ssh key id here'],
            'name': 'db-512mb-sfo1',
            'region': 'sfo1',
            'user_data': 'echo hello jdoe > jdoe_greeting.txt',
            'tags': ['droplet_name:db-512mb-sfo1'],
        })
