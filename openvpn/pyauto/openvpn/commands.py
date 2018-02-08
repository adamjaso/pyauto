import os
import six
import json
from . import config as ovpn_config
from . import connect
from pyauto.pki import config as pki_config
from pyauto.salt_serial import config as salt_config
from pyauto.util import yamlutil


def initialize(config):
    return config.openvpn.initialize()


def vpn_profiles(config):
    return json.dumps(config.openvpn.get_vpn_profiles(), indent=4)


def build_vpn_profiles(config):
    for vp in config.openvpn.get_vpn_profiles():
        print(vp.build())


def show_server_pillar(config, server_id):
    pillar_vars = config.openvpn.get_server(server_id).vpn_profile.get_pillar_vars()
    return json.dumps(pillar_vars, indent=4)


def build_server_pillar(config, server_id):
    pillar_vars = config.openvpn.get_server(server_id).vpn_profile.get_pillar_vars()
    return config.salt_serial.pillar.get_serialized([
        ('openvpn', lambda f, pillar: f.write(yamlutil.dump_dict(pillar_vars)))
    ])


def build_states(config):
    return config.salt_serial.states.get_serialized()


def render_openvpn_template(config, server_id):
    server = config.openvpn.get_server(server_id)
    pillar_vars = server.vpn_profile.get_pillar_vars()

    def write_pillar(f, pillar):
        if six.PY3:
            nonlocal pillar_vars
        pillar_vars = yamlutil.dump_dict(pillar_vars)
        if six.PY3:
            pillar_vars = pillar_vars.encode('utf-8')
        f.write(pillar_vars)

    pillar_str = config.salt_serial.pillar.get_serialized([
        ('openvpn', write_pillar),
    ])
    salt_str = config.salt_serial.states.get_serialized()
    return config.local.render_template(
        'digitalocean_init.sh',
        role='openvpn',
        pillar_str=pillar_str,
        salt_str=salt_str,
        server_name=server.server_name,
    )


def deploy_server(config, server_id):
    return config.openvpn.get_server(server_id).deploy()


def destroy_server(config, server_id):
    return config.openvpn.get_server(server_id).destroy()


def run_client(config, server_id, user_id, device_id):
    d = config.openvpn.get_vpn_profile(server_id, user_id, device_id)
    p = connect.run_command(d.conf_file)
    p.wait()


def get_client_command(config, server_id, user_id, device_id):
    d = config.openvpn.get_vpn_profile(server_id, user_id, device_id)
    cmd = connect.generate_command(d.conf_file)
    print(' '.join(cmd))


if '__main__' == __name__:
    from pyauto import deploy
    deploy.main()
