import re
import os
import six
import hvac
from pyauto.core import config
from pyauto.util import yamlutil


class Vault(config.Config):
    def __init__(self, config, parent=None):
        super(Vault, self).__init__(config, parent)
        self['endpoints'] = [Endpoint(e, self) for e in self.endpoints]
        self['paths'] = [Path(p, self) for p in self.paths]

    def get_endpoint(self, endpoint):
        for ep in self.endpoints:
            if endpoint == ep.get_id():
                return ep
        raise Exception('Unknown endpoint: {0}'.format(endpoint))

    def _get_path(self, *path):
        filename = self.config.local.get_workspace_path(self.directory, *path)
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        return filename

    def get_path(self, path):
        for p in self.paths:
            if path == p.get_id():
                return p
        raise Exception('Unknown path: {0}'.format(path))

    def read_path(self, resource):
        return self.get_path(resource).read()

    def read_path_key(self, resource, key, default=None):
        value = self.read_path(resource)
        return value['data'].get(key, default)


class Endpoint(config.Config):
    client = None

    def get_client(self):
        if self.client is None:
            self.client = hvac.Client(url=self.base_url, verify=self.ssl_verify)
            if 'role_id' in self and 'secret_id' in self:
                self.client.auth_approle(self.role_id, self.secret_id)
            elif 'username' in self and 'password' in self:
                self.client.auth_userpass(self.username, self.password)
            else:
                raise Exception('No authentication provided.')
        return self.client

    def reset(self):
        if self.client is not None:
            self.client.logout()
            self.client = None
        return self


class Path(config.Config):
    def __init__(self, config, parent=None):
        super(Path, self).__init__(config, parent)
        self['path'] = '/'.join([self.get_endpoint().secret_path, self.path])

    @property
    def filename(self, *path):
        return self.config._get_path(self['filename'])

    def get_endpoint(self):
        return self.config.get_endpoint(self.endpoint)

    def read(self):
        client = self.get_endpoint().get_client()
        return client.read(self.path)

    def write(self, **data):
        client = self.get_endpoint().get_client()
        return client.write(self.path, **data)

    def upload_file(self):
        with open(self.filename, 'r') as f:
            data = yamlutil.load_dict(f.read())
            return self.write(**data)

    def download_file(self):
        res = self.read()
        data = yamlutil.dump_dict(res['data'])
        with open(self.filename, 'w') as f:
            f.write(data)
        return self.filename


config.set_config_class('vault', Vault)
