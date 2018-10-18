import os
import pwd
import grp
import json
import shutil
import jmespath
from collections import OrderedDict
from pyauto.core import api
from pyauto.util import strutil, funcutil, yamlutil
from jinja2 import Environment


packages = api.read_packages(__file__, 'package.yml')


def _get_user_id(self):
    if 'uid' in self:
        return self['uid']
    elif 'user' in self:
        return pwd.getpwnam(self['user']).pw_uid
    else:
        return os.getuid()


def _get_group_id(self):
    if 'gid' in self:
        return self['gid']
    elif 'group' in self:
        return grp.getgrnam(self['group']).gr_gid
    else:
        return os.getgid()


class Config(api.KindObject):
    def get_path(self, *fn):
        workspace_dir = os.path.abspath(self.workspace_dir)
        return os.path.normpath(os.path.join(workspace_dir, *fn))

    def init_workspace(self):
        workspace_dir = self.get_path()
        if not os.path.isdir(workspace_dir):
            os.makedirs(workspace_dir)
        return workspace_dir


class Directory(api.KindObject):
    @property
    def mode(self):
        return self.get('mode') or int('755', 8)

    @property
    def uid(self):
        return _get_user_id(self)

    @property
    def gid(self):
        return _get_group_id(self)

    def get_path(self, *path):
        if self.name.startswith(strutil.root_prefix):
            base_path = self.name
        elif self.root:
            base_path = self.root.required.get_path(self.name)
        elif self.directory:
            base_path = self.directory.required.get_path(self.name)
        else:
            base_path = os.path.abspath(self.name)
        return os.path.expanduser(os.path.normpath(
            os.path.join(base_path, *path)))

    def make_dir(self):
        dst = self.get_path()
        if not os.path.isdir(dst):
            os.makedirs(dst)
        return dst

    def remove_dir(self):
        dst = self.get_path()
        if os.path.isdir(dst):
            shutil.rmtree(dst)

    def copy_dir(self, **kwargs):
        source = self.source.required
        ignore = kwargs.get('ignore', [])
        ignore.append('.git')
        ignore.extend(list(source.get('ignore') or []))
        ignore.extend(list(self.get('ignore') or []))
        kwargs['ignore'] = shutil.ignore_patterns(*ignore)
        src_dir = source.get_path()
        dst_dir = self.get_path()
        strutil.copytree(src_dir, dst_dir, **kwargs)
        return dst_dir

    def set_mode(self):
        path = self.get_path()
        os.chmod(path, self.mode)
        return path

    def set_owner(self):
        path = self.get_path()
        os.chown(path, self.uid, self.gid)
        return path

    def load_objects(self, *path):
        self._repo.load_file(self.get_path(*path))


class File(api.KindObject):
    @property
    def mode(self):
        return self.get('mode') or int('644', 8)

    @property
    def uid(self):
        return _get_user_id(self)

    @property
    def gid(self):
        return _get_group_id(self)

    def get_path(self):
        if self.name.startswith(strutil.root_prefix):
            path = self.name
        elif self.root:
            path = self.root.required.get_path(self.name)
        elif self.directory:
            path = self.directory.required.get_path(self.name)
        else:
            path = os.path.abspath(self.name)
        return os.path.expanduser(os.path.normpath(path))

    def get_source_path(self):
        return self.source.required.get_path()

    def remove_file(self):
        filename = self.get_path()
        if os.path.isfile(filename):
            os.remove(filename)

    def copy_file(self):
        src = self.get_source_path()
        dst = self.get_path()
        shutil.copyfile(src, dst)
        return dst

    def set_mode(self):
        path = self.get_path()
        os.chmod(path, self.mode)
        return path

    def set_owner(self):
        path = self.get_path()
        os.chown(path, self.uid, self.gid)
        return path

    def load_objects(self):
        self._repo.load_file(self.get_path())

    def render_template(self):

        def to_yaml(obj, indent=0, skip_first=True, **kwargs):
            result = yamlutil.dump_dict(obj)
            return os.linesep.join([
                (' ' * indent if not skip_first or i != 0 else '') + l
                for i, l in enumerate(result.split(os.linesep))
            ]).strip()

        with open(self.template.required.get_path()) as f:
            env = Environment(
                trim_blocks=True,
                extensions=[
                    'jinja2.ext.do',
                    'jinja2.ext.loopcontrols',
                ])
            env.filters['to_yaml'] = to_yaml
            template = env.from_string(f.read())

        variables = self.resolve_variables()
        data = template.render(**variables)
        dst = self.get_path()
        with open(dst, 'w') as f:
            f.write(data)
        return dst

    def resolve_variables(self):
        context = {}
        for var in self.variables.required:
            values = var.resolve()
            if isinstance(values, api.KindObject):
                values = values.data
            if not isinstance(values, (dict, OrderedDict)):
                raise api.PyautoException('var must resolve to a dict: {0}'
                                          .format(values))
            context.update(values)
        return context


class Variable(api.KindObject):
    def resolve(self):
        value = None
        if self.env:
            if not self.name:
                self['name'] = self.env
            value = self.get_env()
        elif self.file:
            value = self.get_file()
        elif self.function:
            value = self.get_function()
        elif self.map is not None:
            value = self.get_map()
        elif self.variable:
            value = self.variable.required.resolve()
        elif self.string is not None:
            value = self.string
        else:
            raise Exception('unknown variable type: {0}'.format(self))
        if value is None:
            if self.default:
                value = self.default
            elif not self.optional:
                raise Exception('unable to get a value for variable: {0}'
                                .format(self))
        if self.parse:
            if 'json' == self.parse:
                value = json.loads(value)
            elif 'yaml' == self.parse:
                value = yamlutil.load_dict(value)
            else:
                raise Exception('unknown parse type: {0}'.format(self.parse))
        if isinstance(value, (dict, OrderedDict, api.KindObject)) and \
                self.select:
            value = jmespath.search(self.select, value)
        if self.name:
            return {self.name: value}
        else:
            return value

    def get_env(self):
        return os.getenv(self.env)

    def get_file(self):
        filename = self.file.required.get_path()
        with open(filename) as f:
            return f.read()

    def get_function(self):
        return funcutil.Function(self.function).run()

    def get_map(self):
        return self.map
