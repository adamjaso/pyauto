import re
import os
import sys
from . import yamlutil
from .j2util import get_template_renderer

_renderers = {}


def render_file(filename, **kwargs):
    global _renderers
    filename = os.path.abspath(filename)
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    if dirname not in _renderers:
        _renderers[dirname] = get_template_renderer(dirname)
    return _renderers[dirname](basename, **kwargs)


def render_files(values_file, template_files, write, **kwargs):
    concat = kwargs.get('concat', '')
    with open(values_file) as f:
        values = yamlutil.load_dict(f)
    num_template_files = len(template_files)
    for index, tfile in enumerate(template_files):
        data = render_file(tfile, **values).strip() + os.linesep
        if concat and index < num_template_files - 1:
            data += concat + os.linesep
        write(tfile, data)


def render_files_to_stream(values_file, template_files, stream, **kwargs):

    def write(tfile, data):
        if kwargs.get('verbose', False):
            print('rendered {0}'.format(tfile))
        stream.write(data)

    render_files(values_file, template_files, write, **kwargs)


def render_files_to_file(values_file, template_files, output_file, **kwargs):
    with open(output_file, 'w') as f:
        render_files_to_stream(values_file, template_files, f, **kwargs)


def render_files_to_dir(values_file, template_files, output_dir, **kwargs):

    def write(tfile, data):
        name = re.sub('\.j2$', '', os.path.basename(tfile))
        output_file = os.path.join(output_dir, name)
        if kwargs.get('verbose', False):
            print('rendered {0} as {1}'.format(tfile, output_file))
        with open(output_file, 'w') as f:
            f.write(data)

    render_files(values_file, template_files, write, **kwargs)


def main():
    import argparse
    args = argparse.ArgumentParser()
    args.add_argument('-f', '--values',
                      dest='values_file', required=True)
    args.add_argument('-o', '--output',
                      dest='output_file', nargs='?', default='-')
    args.add_argument('-i', '--templates',
                      dest='template_files', nargs='+', default=[])
    args.add_argument('-v', '--verbose', action='store_true')
    args.add_argument('--concat', default='')
    args = args.parse_args()

    output_file = os.path.abspath(args.output_file)
    values_file = os.path.abspath(args.values_file)
    kwargs = {'verbose': args.verbose, 'concat': args.concat}

    if '-' == args.output_file:
        render_files_to_stream(values_file, args.template_files,
                               sys.stdout, **kwargs)

    elif not os.path.isdir(output_file):
        render_files_to_file(values_file, args.template_files,
                             output_file, **kwargs)

    else:
        output_file = output_file or os.getcwd()
        render_files_to_dir(values_file, args.template_files,
                            output_file, **kwargs)


if '__main__' == __name__:
    main()
