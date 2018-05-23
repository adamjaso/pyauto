import os
import json
import shutil
import jmespath
from collections import OrderedDict
from pyauto.core import config, tasks
from pyauto.util import strutil, funcutil, yamlutil
from pyauto.util.j2util import get_template_renderer


class Local(config.Config):
    def __init__(self, config, **kwargs):
        super(Local, self).__init__(config, **kwargs)
        if 'workspace_dir' in self:
            self['workspace_dir'] = self.get_path(self['workspace_dir'])
        if 'template_dir' in self:
            self['template_dir'] = self.get_path(self['template_dir'])
            self.render_template = get_template_renderer(self['template_dir'])
            self['templates'] = [
                Template(t, self) for t in self.get('templates', [])]
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

    def get_template(self, template):
        for t in self.templates:
            if t.get_id() == template:
                return t
        raise Exception('unknown template: {0}'.format(template))

    def get_template_file(self, *fn):
        return os.path.join(self['template_dir'], *fn)

    def get_source_path(self, source_id, *path):
        return self.get_source(source_id).get_path(*path)

    def get_destination_path(self, destination_id, *path):
        return self.get_destination(destination_id).get_path(*path)

    def get_workspace_path(self, *fn):
        return os.path.join(self['workspace_dir'], *fn)

    def get_destination(self, id):
        for dest in self.destinations:
            if dest.get_id() == id:
                return dest
        raise Exception('unknown local.destination: {0}'.format(id))

    def get_source(self, id):
        for src in self.sources:
            if src.get_id() == id:
                return src
        raise Exception('unknown local.source: {0}'.format(id))

    def copytree(self, src_id, dst_id, **kwargs):
        src = self.get_source(src_id)
        src_dir = src.get_path()
        dst_dir = self.get_destination(dst_id).get_path()
        if 'ignore' not in kwargs:
            kwargs['ignore'] = []
        kwargs['ignore'].append('.git')
        kwargs['ignore'].extend(list(src.get('ignore', [])))
        kwargs['ignore'] = shutil.ignore_patterns(*kwargs['ignore'])
        return strutil.copytree(src_dir, dst_dir, **kwargs)

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
        self['templates'] = [
            Template(t, self) for t in self.get('templates', [])]

    def get_template(self, template):
        for t in self.templates:
            if t.get_id() == template:
                return t
        raise Exception('unknown template: {0}'.format(template))

    def get_path(self, *path):
        base_path = self.config.get_workspace_path(self.directory)
        return os.path.join(base_path, *path)

    def copytree(self, **kwargs):
        return self.config.copytree(self.source.get_id(), self.get_id())

    def rmtree(self):
        dst = self.get_path()
        if os.path.isdir(dst):
            shutil.rmtree(dst)

    def get_template_destinations(self):
        return [self.config.get_path(template.destination_filename)
                for template in self.templates]

    def render_templates(self):
        for template in self.templates:
            filename = self.config.get_path(template.destination_filename)
            data = template.render_template()
            with open(filename, 'w') as f:
                f.write(data)


class Template(config.Config):
    def __init__(self, config, parent=None):
        super(Template, self).__init__(config, parent)
        self['variables'] = VariableList(self.variables, self)
        if isinstance(self.config, Destination):
            self.base_template = self.config.config.get_template(self.template)
        else:
            self.base_template = None

    @property
    def template_filename(self):
        if self.base_template:
            return self.base_template.template
        else:
            return self.template

    @property
    def destination_filename(self):
        if self.filename:
            return self.filename
        elif self.base_template:
            return self.base_template.filename
        else:
            raise Exception('No filename found to make destination '
                            'filename for template {0}'
                            .format(self.get_id()))

    def get_context(self, **context):
        context = self.variables.get_context(context)
        if self.base_template is not None:
            context = self.base_template.variables.get_context(context)
        return context

    def render_template(self, **context):
        context = self.get_context(**context)
        if isinstance(self.config, Destination):
            return self.config.config.render_template(
                self.template_filename, **context)
        else:
            return self.config.render_template(
                self.template_filename, **context)


class VariableList(object):
    def __init__(self, variables, parent=None):
        self.config = parent
        self.variables = [Variable(v, parent) for v in variables]

    def get_context(self, context):
        for var in self:
            value = var.get_value()
            if not isinstance(value, (dict, OrderedDict, config.Config)):
                raise Exception('var must resolve to a dict: {0}'
                                .format(value))
            for k, v in value.items():
                if k not in context:
                    context[k] = v
        return context

    def __len__(self):
        return len(self.variables)

    def __iter__(self):
        return iter(self.variables)

    def __getitem__(self, item):
        return self.variables[item]


class Variable(config.Config):
    def get_value(self):
        value = None
        if self.env:
            if not self.name:
                self['name'] = self.env
            value = self.get_env()
        elif self.resource:
            value = self.get_resource()
        elif self.file:
            value = self.get_file()
        elif self.function:
            value = self.get_function()
        elif self.task is not None:
            value = self.run_task()
        elif self.map is not None:
            value = self.get_map()
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
        if isinstance(value, (dict, OrderedDict, config.Config)) and \
                self.select:
            value = jmespath.search(self.select, value)
        if self.name:
            return {self.name: value}
        else:
            return value

    def get_env(self):
        return os.getenv(self.env)

    def get_resource(self):
        if isinstance(self.config.config, Destination):
            return self.config.config.config.config.get_resource(self.resource)
        else:
            return self.config.config.get_resource(self.resource)

    def get_file(self):
        filename = self.config.get_path(self.file)
        with open(filename) as f:
            return f.read()

    def get_function(self):
        return funcutil.Function(self.function).run()

    def get_map(self):
        return self.map

    def run_task(self):
        if isinstance(self.config.config, Destination):
            config = self.config.config.config.config
        else:
            config = self.config.config
        return config.run_task_function(self.task)


config.set_config_class('local', Local)
