import os
import re
import jinja2.ext
from jinja2 import Environment
from jinja2 import FileSystemLoader
from .yamlutil import dump_dict


def get_template_renderer(templates_dirname):
    dirname = templates_dirname
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

    def _render(filename, **kwargs):
        cwd = os.getcwd()
        if filename.startswith(dirname):
            filename = filename.replace(dirname, '')
        filename = re.sub('^/', '', filename)
        kwargs['CURRENT_DIRECTORY'] = cwd
        return env.get_template(filename).render(**kwargs)

    return _render
