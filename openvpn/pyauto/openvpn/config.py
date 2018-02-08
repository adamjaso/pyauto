import os
import netaddr
import shutil
import six
from pyauto.core import config
from pyauto.util import yamlutil, strutil
from pyauto.pki import config as pki_config
from pyauto.digitalocean import config as do_config


salt_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'salt')


class Openvpn(config.Config):
    def __init__(self, config_dict, parent=None):
        super(Openvpn, self).__init__(config_dict, parent)
        self['users'] = [User(u, self) for u in self['users']]
        self['servers'] = [Server(s, self) for s in self['servers']]
        if not self.directory.startswith(strutil.root_prefix):
            self['directory'] = self.config.local.get_workspace_path(self.directory)

    @property
    def ca(self):
        return self.config.pki.get_ca_profile(self['ca'])

    @property
    def user_num_days(self):
        return self.get('user_num_days', 3650)

    @property
    def user_key_size(self):
        return self.get('user_key_size', 2048)

    @property
    def server_num_days(self):
        return self.get('server_num_days', 3650)

    @property
    def server_key_size(self):
        return self.get('server_key_size', 2048)

    @property
    def dh_file(self):
        return self.ca.get_dh_file(self.dh_params_name)

    @property
    def ta_key_file(self):
        return self.ca.get_ta_file(self.ta_key_name)

    def get_server(self, server_id):
        for srv in self.servers:
            if server_id == srv.get_id():
                return srv
        raise Exception('Unknown server: {0}'.format(server_id))

    def get_user(self, user_id):
        for usr in self.users:
            if user_id == usr.get_id():
                return usr
        raise Exception('Unknown user: {0}'.format(user_id))

    def create_profile(self):
        for usr in self.users:
            usr.create_profile()
        for srv in self.servers:
            srv.create_profile()
        return self

    def initialize(self):
        ca = self.ca.init_pki()
        ca.create_dh(self.dh_params_size, self.dh_params_name)
        ca.create_ta_key(self.ta_key_name)
        self.create_profile()
        self.get_file()

    def get_servers_file(self, filename=None):
        return self.get_file(filename, 'server')

    def get_clients_file(self, filename=None):
        return self.get_file(filename, 'client')

    def get_file(self, fn=None, dn=None):
        if dn is not None:
            dn = os.path.join(self.directory, dn)
        else:
            dn = self.directory
        if not os.path.isdir(dn):
            os.makedirs(dn)
        if fn is not None:
            return os.path.join(dn, fn)
        else:
            return dn

    def get_vpn_profile(self, server_id, user_id, device_id):
        for srv in self.servers:
            if server_id == srv.id:
                for usr in srv.users:
                    if user_id == usr.id:
                        dev = usr.get_device(device_id)
                        return VpnProfile(self, srv, dev)
        raise Exception('Unknown vpn profile: {0}-{1}'.format(server_id, dev.id))

    def get_vpn_profiles(self):
        vpn_profiles = []
        for srv in self.servers:
            vpn_profiles.append(VpnProfile(self, srv))
            for usr in srv.users:
                for dev in usr.devices:
                    vpn_profiles.append(VpnProfile(self, srv, dev))
        return vpn_profiles

    def get_base_client_conf(self):
        conf = {}
        conf.update(self.pillar['global'])
        conf.update(self.pillar['client'])
        return conf

    def get_base_server_conf(self):
        conf = {}
        conf.update(self.pillar['global'])
        conf.update(self.pillar['server'])
        net = netaddr.IPNetwork(conf['cidr'])
        network = str(net.network)
        gateway_parts = network.split('.')
        gateway_parts[3] = '1'
        conf['network'] = network
        conf['netmask'] = str(net.netmask)
        conf['gateway'] = '.'.join(gateway_parts)
        return conf


class User(config.Config):
    def __init__(self, config_dict, parent=None):
        super(User, self).__init__(config_dict, parent)
        self['devices'] = [Device(self, dev) for dev in self.devices]

    @property
    def ca(self):
        return self.config.ca

    def create_profile(self):
        for dev in self.devices:
            dev.create_profile()
        return self

    def get_profile_files(self):
        return {dev.id: dev.get_profile_files() for dev in self.devices}

    def get_device(self, name):
        device_id = '.'.join([self.get_id(), name])
        for dev in self['devices']:
            if device_id == dev.id:
                return dev
        raise Exception('Unknown device for user {0}: {1}'.format(self.get_id(), device_id))


class Device(object):
    def __init__(self, user, device_id):
        self.id = '.'.join([user.get_id(), device_id])
        self.name = ' - '.join([user.name, self.id])
        self.user = user

    def create_profile(self):
        openvpn = self.user.config
        self.user.ca.create_profile(
            'client', self.id, self.name, openvpn.user_key_size, openvpn.user_num_days)
        return self

    def get_profile_files(self):
        return self.user.ca.get_profile_files(self.id)


class Server(config.Config):
    def __init__(self, config_dict, parent=None):
        super(Server, self).__init__(config_dict, parent)
        self['users'] = [self.config.get_user(u) for u in self['users']]
        self['vpn_profile'] = VpnProfile(self.config, self)

    @property
    def ca(self):
        return self.config.ca

    def create_profile(self):
        openvpn = self.config
        self.ca.create_profile(
            'server', self.get_id(), self.get_id(), openvpn.server_key_size, openvpn.server_num_days)
        return self

    def get_user(self, user_id):
        if user_id not in [u.get_id() for u in self.users]:
            raise Exception('Unknown server user: {0}-{1}'.format(self.get_id(), user_id))
        return self.config.get_user(user_id)

    def get_profile_files(self):
        return self.ca.get_profile_files(self.get_id())

    def get_pillar_str(self):
        pillar_vars = self.vpn_profile.get_pillar_vars()

        def write_pillar(f, pillar):
            pillar = yamlutil.dump_dict(pillar_vars)
            if six.PY3:
                pillar = pillar.encode('utf-8')
            f.write(pillar)

        return self.config.config.salt_serial.pillar.get_serialized([
            ('openvpn', write_pillar)
        ])

    def get_states_str(self):
        return self.config.config.salt_serial.states.get_serialized()

    def deploy(self, **kwargs):
        config = self.config.config
        pillar_vars = self.vpn_profile.get_pillar_vars()

        def write_pillar(f, pillar):
            if six.PY3:
                nonlocal pillar_vars
            pillar_vars = yamlutil.dump_dict(pillar_vars)
            if six.PY3:
                pillar_vars = pillar_vars.encode('utf-8')
            f.write(pillar_vars)

        pillar_str = config.salt_serial.pillar.get_serialized([
            ('openvpn', write_pillar)
        ])
        salt_str = config.salt_serial.states.get_serialized()
        user_data = config.local.render_template(
            'digitalocean_init.sh',
            role='openvpn',
            pillar_str=pillar_str,
            salt_str=salt_str,
            server_name=self.server_name,
        )
        droplet = do_config.Droplet(self.digitalocean, config.digitalocean)
        return droplet.deploy(user_data=user_data)

    def destroy(self):
        droplet = do_config.Droplet(self.digitalocean, self.config.config.digitalocean)
        return droplet.destroy()


class VpnProfile(dict):
    is_server = False

    def __init__(self, openvpn, server, device=None):
        super(VpnProfile, self).__init__()
        self.openvpn = openvpn
        self.is_server = device is None
        server_id = server.get_id()
        if self.is_server:
            self.id = server_id
            self.src = server.get_profile_files()
            self.update(openvpn.get_base_server_conf())
            self.update(server.get('openvpn', {}))
            self['profile'] = 'server'
        else:
            self.id = '-'.join([server_id, device.id])
            self.src = device.get_profile_files()
            self.update(openvpn.get_base_client_conf())
            self['profile'] = 'client'
            self['server_host'] = server.server_name
        self.get_file()
        self.conf_template = '.'.join([self['profile'], 'conf', 'j2'])
        self['ca_cert_file'] = 'ca.crt'
        self['ta_key_file'] = 'ta.key'
        self['dh_file'] = 'dh.pem'
        self['key_file'] = '.'.join([self['profile'], 'key'])
        self['cert_file'] = '.'.join([self['profile'], 'crt'])
        self['conf_file'] = '.'.join([server['server_name'], 'conf'])
        self['ovpn_file'] = '.'.join([server['server_name'], 'ovpn'])

    def match(self, server_id, user_id, device_id):
        _id = ''.join([server_id, '-', user_id, '.', device_id])
        return 'client' == self['profile'] and _id == self.id

    def get_file(self, fn=None):
        return self.openvpn.get_file(fn, os.path.join(self['profile'], self.id))

    @property
    def ca_cert_file(self):
        return self.get_file(self['ca_cert_file'])

    @property
    def dh_file(self):
        return self.get_file(self['dh_file'])

    @property
    def ta_key_file(self):
        return self.get_file(self['ta_key_file'])

    @property
    def conf_file(self):
        return self.get_file(self['conf_file'])

    @property
    def ovpn_file(self):
        return self.get_file(self['ovpn_file'])

    @property
    def key_file(self):
        return self.get_file(self['key_file'])

    @property
    def cert_file(self):
        return self.get_file(self['cert_file'])

    @property
    def src_ca_cert_file(self):
        return self.src['ca_cert_file']

    @property
    def src_dh_file(self):
        return self.openvpn.dh_file

    @property
    def src_ta_key_file(self):
        return self.openvpn.ta_key_file

    @property
    def src_key_file(self):
        return self.src['key_file']

    @property
    def src_cert_file(self):
        return self.src['cert_file']

    @property
    def ca_cert(self):
        with open(self.ca_cert_file) as f:
            return f.read().strip()

    @property
    def key(self):
        with open(self.key_file) as f:
            return f.read().strip()

    @property
    def cert(self):
        with open(self.cert_file) as f:
            return f.read().strip()

    @property
    def ta_key(self):
        with open(self.ta_key_file) as f:
            return f.read().strip()

    @property
    def dh(self):
        with open(self.dh_file) as f:
            return f.read().strip()

    def build(self):
        for k in ['ta_key', 'dh', 'key', 'ca_cert', 'cert']:
            src_file = getattr(self, '_'.join(['src', k, 'file']))
            dst_file = getattr(self, '_'.join([k, 'file']))
            shutil.copy(src_file, dst_file)
        with open(self.conf_file, 'w') as f:
            f.write(self.render())
        with open(self.ovpn_file, 'w') as f:
            f.write(self.render_ovpn())
        return self.conf_file

    def render(self):
        return self.openvpn.config.local.render_template(self.conf_template, **self)

    def render_ovpn(self):
        conf_text = self.render()
        return os.linesep.join([
            conf_text, '',
            '<tls-auth>', self.ta_key, '</tls-auth>',
            '<ca>', self.ca_cert, '</ca>',
            '<cert>', self.cert, '</cert>',
            '<key>', self.key, '</key>',
        ])

    def get_pillar_vars(self):
        return dict(
            port=self.get('port'),
            protocol=self.get('protocol'),
            cidr=self.get('cidr'),
            servers=[self.get_pillar_entry()]
        )

    def get_pillar_entry(self):
        with open(self.conf_file) as f:
            conf = f.read()
        with open(self.cert_file) as f:
            cert = f.read()
        with open(self.key_file) as f:
            key = f.read()
        with open(self.ca_cert_file) as f:
            ca_cert = f.read()
        with open(self.ta_key_file) as f:
            ta_key = f.read()
        with open(self.dh_file) as f:
            dh_params = f.read()
        return dict(
            id=self.id,
            conf_filename=self['conf_file'],
            conf=conf,
            cert_filename=self['cert_file'],
            cert=cert,
            key_filename=self['key_file'],
            key=key,
            ca_cert_filename=self['ca_cert_file'],
            ca_cert=ca_cert,
            ta_key_filename=self['ta_key_file'],
            ta_key=ta_key,
            dh_params_filename=self['dh_file'],
            dh_params=dh_params,
        )


config.set_config_class('openvpn', Openvpn)
