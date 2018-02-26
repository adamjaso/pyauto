import os
import re
import jinja2.ext
from jinja2 import Environment
from jinja2 import FileSystemLoader
from .yamlutil import dump_dict


def build_env(dirname):
    env = Environment(
        loader=FileSystemLoader(dirname),
        trim_blocks=True,
        extensions=[
            'jinja2.ext.do',
            'jinja2.ext.loopcontrols',
        ],
    )

    def to_yaml(obj, indent=0, skip_first=True, **kwargs):
        result = dump_dict(obj)
        return os.linesep.join([
            (' ' * indent if not skip_first or i != 0 else '') + l
            for i, l in enumerate(result.split(os.linesep))
        ]).strip()

    env.filters['to_yaml'] = to_yaml
    return env


def get_template_renderer(templates_dirname):
    env = build_env(templates_dirname)

    def _render(filename_, **kwargs):
        cwd = os.getcwd()
        if filename_.startswith(templates_dirname):
            filename_ = filename_.replace(templates_dirname, '')
        filename_ = re.sub('^/', '', filename_)
        kwargs['CURRENT_DIRECTORY'] = cwd
        return env.get_template(filename_).render(**kwargs)

    return _render
