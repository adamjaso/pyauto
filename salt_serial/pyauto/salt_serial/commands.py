from pyauto.util import yamlutil
from . import config as salt_config


def serialize_pillar(config):
    def get_openvpn_vars(f, pillar):
        f.write(yamlutil.dump_dict(dict(
            servers=[],
            clients=[],
        )))
    return config.salt.pillar.get_serialized([
        ('openvpn', get_openvpn_vars)
    ])


def serialize_states(config):
    return config.salt.states.get_serialized()
