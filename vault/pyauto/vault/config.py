import os
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

    def __init__(self, config, parent=None):
        super(Endpoint, self).__init__(config, parent)
        if 'base_url' not in self and 'base_url_env' in self:
            self['base_url'] = os.getenv(self['base_url_env'])
        if 'secret_path' not in self and 'secret_path_env' in self:
            self['secret_path'] = os.getenv(self['secret_path_env'])
        if 'ssl_verify' not in self and 'ssl_verify_env' in self:
            self['ssl_verify'] = \
                os.getenv('ssl_verify_env', 'true').strip().lower() == 'true'
        if 'role_id' not in self and 'role_id_env' in self:
            self['role_id'] = os.getenv(self['role_id_env'])
        if 'secret_id' not in self and 'secret_id_env' in self:
            self['secret_id'] = os.getenv(self['secret_id_env'])
        if 'username_env' in self:
            self['username'] = os.getenv(self['username_env'])
        if 'password_env' in self:
            self['password'] = os.getenv(self['password_env'])

    def get_client(self):
        if self.client is None:
            self.client = hvac.Client(
                url=self.base_url, verify=self.ssl_verify)
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

    @property
    def mapping(self):
        return {
            name: self.config.config.get_resource(self['mapping'][name])
            for name, value in self['mapping'].items()
        }

    def get_endpoint(self):
        return self.config.get_endpoint(self.endpoint)

    def read(self):
        client = self.get_endpoint().get_client()
        return client.read(self.path)

    def write(self, **data):
        client = self.get_endpoint().get_client()
        return client.write(self.path, **data)

    def save_mapping(self, data):
        if 'mapping' in self:
            filenames = {}
            for name, filename in self.mapping.items():
                filenames[name] = filename
                value = data[name]
                with open(filename, 'w') as f:
                    f.write(value)
            return self.mapping
        else:
            data = yamlutil.dump_dict(data, safe_dump=True)
            with open(self.filename, 'w') as f:
                f.write(data)
            return self.filename

    def load_mapping(self):
        result = {}
        if 'mapping' in self:
            for name, filename in self.mapping.items():
                with open(filename, 'r') as f:
                    result[name] = f.read()
            return result
        else:
            with open(self.filename, 'r') as f:
                data = yamlutil.load_dict(f.read())
                return data

    def upload_file(self):
        data = self.load_mapping()
        return self.write(**data)

    def download_file(self):
        res = self.read()
        return self.save_mapping(res['data'])


config.set_config_class('vault', Vault)
