import re
import os
import sys
from pyauto.util import yamlutil
from pyauto.util.j2util import build_env
from pyauto.core import taskgen
from collections import OrderedDict

_renderers = {}


def get_template_renderer(templates_dirname):
    env = build_env(templates_dirname)
    env.filters['generate_tasks'] = taskgen.generate_tasks

    def _render(filename_, **kwargs):
        if filename_.startswith(templates_dirname):
            filename_ = filename_.replace(templates_dirname, '')
        filename_ = re.sub('^/', '', filename_)
        if 'CURRENT_DIRECTORY' not in kwargs:
            kwargs['CURRENT_DIRECTORY'] = os.getcwd()
        return env.get_template(filename_).render(**kwargs)

    return _render


def render_file(filename, **kwargs):
    global _renderers
    filename = os.path.abspath(filename)
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    if dirname not in _renderers:
        _renderers[dirname] = get_template_renderer(dirname)
    return _renderers[dirname](basename, **kwargs)


def render_files(values, template_files, write, **kwargs):
    concat = kwargs.get('concat', '')
    num_template_files = len(template_files)
    for index, tfile in enumerate(template_files):
        data = render_file(tfile, **values).strip() + os.linesep
        if concat and index < num_template_files - 1:
            data += concat + os.linesep
        write(tfile, data)


def render_files_to_stream(values, template_files, stream, **kwargs):

    def write(tfile, data):
        if kwargs.get('verbose', False):
            print('rendered {0}'.format(tfile))
        stream.write(data)

    render_files(values, template_files, write, **kwargs)


def render_files_to_file(values, template_files, output_file, **kwargs):
    with open(output_file, 'w') as f:
        render_files_to_stream(values, template_files, f, **kwargs)


def render_files_to_dir(values, template_files, output_dir, **kwargs):

    def write(tfile, data):
        name = re.sub('\.j2$', '', os.path.basename(tfile))
        output_file = os.path.join(output_dir, name)
        if kwargs.get('verbose', False):
            print('rendered {0} as {1}'.format(tfile, output_file))
        with open(output_file, 'w') as f:
            f.write(data)

    render_files(values, template_files, write, **kwargs)


def build_values(values_files):
    values_files = [os.path.abspath(p) for p in values_files]
    values = OrderedDict()
    for values_file in values_files:
        with open(values_file) as f:
            values.update(yamlutil.load_dict(f))
    return values


def main():
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument('-f', '--values',
                      dest='values_files', nargs='+', required=True)
    args.add_argument('-o', '--output',
                      dest='output_file', nargs='?', default='-')
    args.add_argument('-i', '--templates',
                      dest='template_files', nargs='+', default=[])
    args.add_argument('-v', '--verbose', action='store_true')
    args.add_argument('--concat', default='')
    args = args.parse_args()

    output_file = os.path.abspath(args.output_file)
    values = build_values(args.values_files)

    kwargs = {'verbose': args.verbose, 'concat': args.concat}

    if '-' == args.output_file:
        render_files_to_stream(values, args.template_files,
                               sys.stdout, **kwargs)

    elif not os.path.isdir(output_file):
        render_files_to_file(values, args.template_files,
                             output_file, **kwargs)

    else:
        output_file = output_file or os.getcwd()
        render_files_to_dir(values, args.template_files,
                            output_file, **kwargs)


if '__main__' == __name__:
    main()
