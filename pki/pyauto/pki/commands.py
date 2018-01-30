import os
from pyauto.core import config
from pyauto.local import config as local_config
from . import pkiutil as pki
from . import config as pki_config


def init_pki(config, ca):
    return config.pki.get_ca_profile(ca).init_pki()


def create_key(config, ca, key_size, profile_id, passphrase=None):
    return config.pki.get_ca_profile(ca).create_key(profile_id, key_size, passphrase)


def create_req(config, ca, cert_type, profile_id, common_name, passphrase=None):
    return config.pki.get_ca_profile(ca).create_req(cert_type, common_name, profile_id, profile_id, passphrase)


def create_cert(config, ca, profile_id, num_days):
    return config.pki.get_ca_profile(ca).create_cert(profile_id, profile_id, num_days)


def revoke_cert(config, profile_id):
    return config.pki.get_profile(profile_id).revoke()


def create_profile_from_details(config, ca, cert_type, profile_id, common_name, key_size, num_days, passphrase=None):
    return config.pki.get_ca_profile(ca).create_profile(cert_type, profile_id, common_name, key_size, num_days, passphrase)


def create_profile(config, profile_id):
    return config.pki.get_profile(profile_id).create()


def create_dh(config, ca, key_size, dh_file):
    return config.pki.get_ca_profile(ca).create_dh(key_size, dh_file)


def create_openvpn_ta_key(config, ca, key_file):
    return config.pki.get_ca_profile(ca).create_ta_key(key_file)


if '__main__' == __name__:
    from pyauto.core import deploy
    deploy.main()
