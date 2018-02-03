import os
import shutil
from unittest import TestCase
from pyauto.core import deploy, config
from pyauto.openvpn import config as openvpn_config
from pyauto.pki import config as pki_config
from pyauto.local import config as local_config
from pyauto.salt_serial import config as salts_config
config.set_id_key('id')
dirname = os.path.dirname(os.path.abspath(__file__))
conf = deploy.Command(os.path.join(dirname, 'config.yml'), []).config
pki = conf.pki
local = conf.local
openvpn = conf.openvpn

server_id = 'vpn1-sfo1'
user_id = 'turbo'
device_id = 'phone'


def setUpModule():
    local.init_workspace()
    openvpn.initialize()


def tearDownModule():
    dn = local.get_workspace_path()
    if os.path.isdir(dn):
        shutil.rmtree(dn)


class Openvpn(TestCase):
    def test_ca_getter(self):
        self.assertIsInstance(openvpn.ca, pki_config.CAProfile)

    def test_get_server(self):
        s = openvpn.get_server(server_id)
        self.assertIsInstance(s, openvpn_config.Server)

    def test_get_user(self):
        u = openvpn.get_user(user_id)
        self.assertIsInstance(u, openvpn_config.User)

    def test_get_servers_file(self):
        fn = openvpn.get_servers_file()
        self.assertTrue(os.path.isdir(fn))

    def test_get_clients_file(self):
        fn = openvpn.get_clients_file()
        self.assertTrue(os.path.isdir(fn))

    def test_get_vpn_profile(self):
        vp = openvpn.get_vpn_profile(server_id, user_id, device_id)
        self.assertIsInstance(vp, openvpn_config.VpnProfile)

    def test_get_vpn_profiles(self):
        vps = openvpn.get_vpn_profiles()
        self.assertIsInstance(vps, list)
        self.assertIsInstance(vps[0], openvpn_config.VpnProfile)


class User(TestCase):
    def setUp(self):
        self.user = openvpn.get_user(user_id)

    def tearDown(self):
        self.user = None

    def test_ca_getter(self):
        self.assertIsInstance(self.user.ca, pki_config.CAProfile)

    def test_get_device(self):
        d = self.user.get_device(device_id)
        self.assertIsInstance(d, openvpn_config.Device)


class Device(TestCase):
    def setUp(self):
        self.device = openvpn.get_user(user_id).get_device(device_id)

    def tearDown(self):
        self.device = None

    def test_get_profile_files(self):
        for fn in self.device.get_profile_files().values():
            self.assertTrue(os.path.isfile(fn))


class Server(TestCase):
    def setUp(self):
        self.server = openvpn.get_server(server_id)

    def tearDown(self):
        self.server = None

    def test_init(self):
        self.assertIsInstance(self.server.users, list)
        self.assertIsInstance(self.server.users[0], openvpn_config.User)
        self.assertIsInstance(self.server.vpn_profile,
                              openvpn_config.VpnProfile)

    def test_ca_getter(self):
        self.assertIsInstance(self.server.ca, pki_config.CAProfile)

    def test_get_user(self):
        u = self.server.get_user(user_id)
        self.assertIsInstance(u, openvpn_config.User)
        with self.assertRaises(Exception):
            self.server.get_user('turbo2')

    def test_get_pillar_str(self):
        self.server.vpn_profile.build()
        self.server.create_profile()
        self.server.get_pillar_str()

    def test_get_states_str(self):
        self.server.vpn_profile.build()
        self.server.create_profile()
        self.server.get_states_str()


class VpnProfile(TestCase):
    def setUp(self):
        self.server = openvpn.get_server(server_id).vpn_profile
        self.client = openvpn.get_vpn_profile(server_id, user_id, device_id)

    def tearDown(self):
        self.server = None
        self.client = None

    def test_build_client(self):
        self.client.build()
        self.assertTrue(os.path.isfile(self.client.conf_file))
        self.assertTrue(os.path.isfile(self.client.ovpn_file))

    def test_build_server(self):
        self.server.build()
        self.assertTrue(os.path.isfile(self.server.conf_file))
        self.assertTrue(os.path.isfile(self.server.ovpn_file))

    def test_get_pillar_vars(self):
        self.client.get_pillar_vars()
        self.server.get_pillar_vars()

    def test_get_pillar_entry(self):
        self.client.get_pillar_entry()
        self.server.get_pillar_entry()

