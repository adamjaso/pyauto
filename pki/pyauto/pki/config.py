import os
from . import pkiutil as pki
from pyauto.core import config
from pyauto.local import config as local_config


class PKI(config.Config):
    def __init__(self, config_dict, parent=None):
        super(PKI, self).__init__(config_dict, parent)
        self['ca_profiles'] = [CAProfile(cap, self) for cap in self['ca_profiles']]
        self['profiles'] = [Profile(p, self) for p in self['profiles']]

    def get_ca_profile(self, profile_id):
        for profile in self.ca_profiles:
            if profile_id == profile[config._id_key]:
                return profile
        raise Exception('Unknown CA Profile: {0}'.format(profile_id))

    def get_profile(self, profile_id):
        for profile in self.profiles:
            if profile_id == profile[config._id_key]:
                return profile
        raise Exception('Unknown Profile: {0}'.format(profile_id))


class CAProfile(config.Config):
    def init_pki(self):
        config = self.config.config
        req = config.local.get_workspace_path(self.directory, self.reqs_dir)
        prv = config.local.get_workspace_path(self.directory, self.private_dir)
        crt = config.local.get_workspace_path(self.directory, self.certs_dir)
        vpn = config.local.get_workspace_path(self.directory, self.openvpn_dir)
        if not os.path.isdir(req):
            os.makedirs(req)
        if not os.path.isdir(prv):
            os.makedirs(prv)
        if not os.path.isdir(crt):
            os.makedirs(crt)
        if not os.path.isdir(vpn):
            os.makedirs(vpn)
        self.create_ca()
        return self

    # CA Settings

    @property
    def passphrase(self):
        return self.get('passphrase', None)

    @property
    def ca_key_size(self):
        return self.get('ca_key_size', 4096)

    @property
    def ca_num_days(self):
        return self.get('ca_num_days', 3650)

    @property
    def crl_name(self):
        return self.get('crl_name', 'ca')

    @property
    def ca_cert_name(self):
        return self.get('ca_cert_name', 'ca')

    @property
    def ca_key_name(self):
        return self.get('ca_key_name', 'ca')

    @property
    def crl_file(self):
        return self.get_global_file(self.crl_name, 'crl')

    @property
    def ca_cert_file(self):
        return self.get_global_file(self.ca_cert_name, 'crt')

    @property
    def ca_key_file(self):
        return self.get_global_file(self.ca_key_name, 'key')

    @property
    def crl(self):
        return pki.CRL().set_file(self.crl_file)

    @property
    def ca_key(self):
        return pki.RSAKey().set_passphrase(self.passphrase).set_file(self.ca_key_file)

    @property
    def ca_cert(self):
        return pki.Cert().set_file(self.ca_cert_file)

    def create_ca(self):

        # create ca key

        ca_key_file = self.ca_key_file
        ca_key = self.ca_key
        if os.path.isfile(ca_key_file):
            ca_key.load()
        else:
            ca_key.generate(self.ca_key_size).save()

        # create ca cert

        ca_cert_file = self.ca_cert_file
        ca_cert = self.ca_cert
        if os.path.isfile(ca_cert_file):
            ca_cert.load()
        else:
            ca_cert.create_ca(self.common_name, self.ca_num_days, ca_key).save()

        # create crl

        crl_file = self.crl_file
        crl = self.crl
        if os.path.isfile(crl_file):
            crl.load()
        else:
            crl.initialize(ca_key, ca_cert).save()

        ca_crl_file = self.join_ca_crl()
        return ca_key, ca_cert, crl, ca_crl_file

    # Other CA Settings

    def get_file(self, dn, fn, ext):
        if not fn.startswith('/'):
            if not fn.endswith(ext):
                fn = '.'.join([fn, ext])
            if dn is not None:
                fn = os.path.sep.join([dn, fn])
        return self.config.config.local.get_workspace_path(self.directory, fn)

    def get_key_file(self, fn):
        return self.get_file(self.private_dir, fn, 'key')

    def get_req_file(self, fn):
        return self.get_file(self.reqs_dir, fn, 'req')

    def get_cert_file(self, fn):
        return self.get_file(self.certs_dir, fn, 'crt')

    def get_dh_file(self, fn):
        return self.get_file(self.openvpn_dir, fn, 'pem')

    def get_ta_file(self, fn):
        return self.get_file(self.openvpn_dir, fn, 'key')

    def get_global_file(self, fn, ext):
        return self.get_file(None, fn, ext)

    def load_key(self, key_file, passphrase=None):
        key_file = self.get_key_file(key_file)
        return pki.RSAKey().set_passphrase(passphrase).set_file(key_file).load()

    def load_req(self, csr_file):
        csr_file = self.get_req_file(csr_file)
        return pki.CSR().set_file(csr_file).load()

    def load_cert(self, cert_file):
        cert_file = self.get_cert_file(cert_file)
        return pki.Cert().set_file(cert_file).load()

    def load_crl(self, crl_file):
        crl_file = self.get_global_file(crl_file, 'crl')
        return pki.CRL().set_file(crl_file).load()

    def load_dh(self, dh_file):
        dh_file = self.get_dh_file(dh_file)
        return pki.DHParam().set_file(dh_file).load()

    def load_ta_key(self, ta_key_file):
        openvpn_bin = self.config.openvpn_bin
        ta_key_file = self.get_ta_file(ta_key_file)
        return pki.TAKey().set_file(ta_key_file).set_openvpn_path(openvpn_bin)

    def create_key(self, key_file, key_size, passphrase=None):
        key_file = self.get_key_file(key_file)
        key = pki.RSAKey().set_passphrase(passphrase).set_file(key_file)
        if not os.path.isfile(key_file):
            key.generate(key_size).save()
        else:
            key.load()
        return key

    def create_req(self, cert_type, common_name, key_file, csr_file, passphrase=None):
        csr_file = self.get_req_file(csr_file)
        if os.path.isfile(csr_file):
            return self.load_req(csr_file)

        key = self.load_key(key_file, passphrase)
        csr = pki.CSR().set_file(csr_file)
        if 'subca' == cert_type:
            return csr.create_subca(common_name, key).save()
        elif 'server' == cert_type:
            return csr.create_server(common_name, key).save()
        elif 'client' == cert_type:
            return csr.create_client(common_name, key).save()
        else:
            raise Exception('Invalid cert type: {0}'.format(cert_type))

    def create_cert(self, csr_file, cert_file, num_days=None):
        num_days = num_days or self.default_num_days
        cert_file = self.get_cert_file(cert_file)
        if os.path.isfile(cert_file):
            return self.load_cert(cert_file)
        csr = self.load_req(csr_file)
        ca_key = self.ca_key.load()
        ca_cert = self.ca_cert.load()

        cert = pki.Cert().set_file(cert_file).create(csr, ca_key, ca_cert, num_days).save()
        return cert

    def revoke_cert(self, cert_file):
        crl = self.crl.load()
        ca_key = self.ca_key.load()
        ca_cert = self.ca_cert.load()
        cert = self.load_cert(cert_file)
        return crl.revoke_cert(cert, ca_key, ca_cert).save()

    def revoke_cert_and_bundle(self, cert_file):
        crl = self.revoke_cert(cert_file)
        ca_crl = self.join_ca_crl()
        return crl, ca_crl

    def join_ca_crl(self):
        ca_file = self.ca_cert_file
        crl_file = self.crl_file
        ca_crl_file = self.get_global_file('ca-crl-bundle', 'pem')
        ca_crl = []
        with open(ca_file) as f:
            ca_crl.append(f.read().strip())
        with open(crl_file) as f:
            ca_crl.append(f.read().strip())
        with open(ca_crl_file, 'w') as f:
            f.write(os.linesep.join(ca_crl))
        return ca_crl_file

    def create_profile(self, cert_type, client_id, common_name, key_size, num_days=None, passphrase=None):
        key = self.create_key(client_id, key_size, passphrase)
        csr = self.create_req(cert_type, common_name, client_id, client_id, passphrase)
        cert = self.create_cert(client_id, client_id, num_days)
        return key, csr, cert

    def get_profile_files(self, profile_id, include_req=False):
        files = dict(
            key_file=self.get_key_file(profile_id),
            cert_file=self.get_cert_file(profile_id),
            ca_cert_file=self.ca_cert_file,
        )
        if include_req:
            files['req_file'] = self.get_req_file(profile_id)
        return files

    def create_dh(self, key_size, dh_file):
        dh_file = self.get_dh_file(dh_file)
        if os.path.isfile(dh_file):
            return self.load_dh(dh_file)
        dhparam = pki.DHParam().set_file(dh_file).generate(key_size).save()
        return dhparam

    def create_ta_key(self, key_file):
        _key_file = self.get_ta_file(key_file)
        ta_key = self.load_ta_key(key_file)
        if os.path.isfile(_key_file):
            return ta_key
        return ta_key.generate()


class Profile(config.Config):

    @property
    def common_name(self):
        return self.get('common_name', self.id)

    @property
    def num_days(self):
        return self.get('num_days', 3650)

    @property
    def key_size(self):
        return self.get('key_size', 2048)

    @property
    def passphrase(self):
        return self.get('passphrase', None)

    @property
    def ca_profile(self):
        return self.config.get_ca_profile(self.ca)

    @property
    def key_file(self):
        return self.ca_profile.get_key_file(self.id)

    @property
    def cert_file(self):
        return self.ca_profile.get_cert_file(self.id)

    @property
    def req_file(self):
        return self.ca_profile.get_req_file(self.id)

    @property
    def key(self):
        return self.ca_profile.load_key(self.id, self.passphrase)

    @property
    def cert(self):
        return self.ca_profile.load_cert(self.id)

    @property
    def req(self):
        return self.ca_profile.load_req(self.id)

    def create(self):
        return self.ca_profile.create_profile(self.profile, self.id, self.common_name, self.key_size, self.num_days, self.passphrase)

    def revoke(self):
        return self.ca_profile.revoke_cert(self.id)


config.set_config_class('pki', PKI)
