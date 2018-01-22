import os, shutil
from pyauto.core import config
from pyauto.util import strutil
from pyauto.util.j2util import get_template_renderer


class Local(config.Config):
    def __init__(self, config, **kwargs):
        super(Local, self).__init__(config, **kwargs)
        if 'workspace_dir' in self:
            self['workspace_dir'] = self.get_path(self['workspace_dir'])
        if 'template_dir' in self:
            self['template_dir'] = self.get_path(self['template_dir'])
            self.render_template = get_template_renderer(self['template_dir'])
        if 'sources' in self:
            self['sources'] = [
                Source(s, self) for s in self['sources']]
        if 'destinations' in self:
            self['destinations'] = [
                Destination(d, self) for d in self['destinations']]

    def init_workspace(self):
        workspace_dir = self.get_workspace_path()
        if not os.path.isdir(workspace_dir):
            os.makedirs(workspace_dir)

    def get_template_file(self, *fn):
        return os.path.join(self['template_dir'], *fn)

    def get_workspace_path(self, *fn):
        return os.path.join(self['workspace_dir'], *fn)

    def get_destination(self, id):
        for dest in self.destinations:
            if dest.id == id:
                return dest
        raise Exception('unknown local.destination: {0}'.format(id))

    def get_source(self, id):
        for src in self.sources:
            if src.id == id:
                return src
        raise Exception('unknown local.source: {0}'.format(id))

    def copytree(self, src_id, dst_id, **kwargs):
        src = self.get_source(src_id).get_path()
        dst = self.get_destination(dst_id).get_path()
        return strutil.copytree(src, dst, **kwargs)

    def rmtree(self, dst_id):
        return self.get_destination(dst_id).rmtree()


class Source(config.Config):
    def get_path(self, *path):
        base_path = self.config.config.get_path(self.directory)
        return os.path.join(base_path, *path)


class Destination(config.Config):
    def __init__(self, config, parent=None):
        super(Destination, self).__init__(config, parent)
        if 'source' in self:
            self['source'] = self.config.get_source(self['source'])

    def get_path(self, *path):
        base_path = self.config.get_workspace_path(self.directory)
        return os.path.join(base_path, *path)

    def copytree(self, **kwargs):
        return self.config.copytree(self.source.id, self.id)

    def rmtree(self):
        dst = self.get_path()
        if os.path.isdir(dst):
            shutil.rmtree(dst)


config.set_config_class('local', Local)
