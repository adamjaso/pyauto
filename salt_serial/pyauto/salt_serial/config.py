import os
import tarfile
import six
from six import StringIO
from io import BytesIO
from uuid import uuid4
from base64 import b64encode
from pyauto.core import config
from pyauto.util import gzutil, yamlutil
from pyauto.local import config as local_config


class Salt(config.Config):
    def __init__(self, config_dict, parent=None):
        super(Salt, self).__init__(config_dict, parent)
        self['pillar'] = Pillar(self['pillar'], self)
        self['states'] = States(self['states'], self)
        self['directory'] = self.config.local.get_template_file(self.directory)

    def new_tmp_file(self, ext='sls'):
        return self.config.local.get_workspace_path(
            '.'.join([str(uuid4()), ext]))

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


class States(config.Config):
    def get_directory(self):
        return self.config.get_file(dn=self.directory)

    def get_serialized(self):
        local_salt_dir = self.get_directory()
        tmp_file = self.config.new_tmp_file('tar.gz')
        try:
            with tarfile.open(tmp_file, 'w:gz') as tf:
                for dp, dns, fns in os.walk(local_salt_dir):
                    for dn in dns:
                        an = os.path.join(dp, dn).replace(local_salt_dir, '')
                        tf.add(os.path.join(dp, dn), arcname=an)
                    for fn in fns:
                        an = os.path.join(dp, fn).replace(local_salt_dir, '')
                        tf.add(os.path.join(dp, fn), arcname=an)

            o = BytesIO()
            with open(tmp_file, 'rb') as f:
                gzutil.compress_stream(f, o)
        finally:
            os.unlink(tmp_file)
        data = b64encode(o.getvalue())
        if not six.PY3:
            return data
        else:
            return data.decode('utf-8')


class Pillar(config.Config):
    def __init__(self, config_dict, parent=None):
        super(Pillar, self).__init__(config_dict, parent)

    def get_serialized(self, states):
        tar_file = self.config.new_tmp_file('tar.gz')
        try:
            with tarfile.open(tar_file, 'w:gz') as tf:
                top_file = self.config.new_tmp_file()
                with open(top_file, 'w') as f:
                    f.write(yamlutil.dump_dict(dict(base={'*': [
                        state[0] for state in states]})))
                tf.add(top_file, arcname='top.sls')
                os.unlink(top_file)
                for state, func in states:
                    tmp_file = self.config.new_tmp_file()
                    arc_name = '.'.join([state, 'sls'])
                    with open(tmp_file, 'wb') as f:
                        func(f, self)
                    tf.add(tmp_file, arcname=arc_name)
                    os.unlink(tmp_file)
            o = BytesIO()
            with open(tar_file, 'rb') as f:
                gzutil.compress_stream(f, o)
        finally:
            os.unlink(tar_file)
        data = b64encode(o.getvalue())
        if not six.PY3:
            return data
        else:
            return data.decode('utf-8')


config.set_config_class('salt_serial', Salt)
