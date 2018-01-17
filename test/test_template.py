import os
import yaml
from six import StringIO
from pyauto import template
from unittest import TestCase

template_example_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'template-example')
template_dir = os.path.join(template_example_dir, 'templates')
output_dir = os.path.join(template_example_dir, 'output')
test1_template = os.path.join(template_dir, 'test1.yml.j2')
test2_template = os.path.join(template_dir, 'test2.yml.j2')
test_file = os.path.join(output_dir, 'test.yml')
test1_file = os.path.join(output_dir, 'test1.yml')
test2_file = os.path.join(output_dir, 'test2.yml')
values_file = os.path.join(template_example_dir, 'values.yml')
template_files = [test1_template, test2_template]


def concat_tests():
    output = StringIO()
    with open(test1_file) as f:
        output.write(f.read())
    with open(test2_file) as f:
        output.write(f.read())
    return output.getvalue()


def clear_output_dir():
    if os.path.isfile(test_file):
        os.remove(test_file)
    if os.path.isfile(test1_file):
        os.remove(test1_file)
    if os.path.isfile(test2_file):
        os.remove(test2_file)


class TestTemplateRenderFiles(TestCase):
    def test_render_file(self):
        template.render_files_to_dir(values_file, template_files, output_dir)
        with open(values_file) as f:
            values = yaml.load(f)
        rendered = template.render_file(test1_template, **values).strip()
        with open(test1_file) as f:
            data = f.read().strip()
            self.assertEqual(data, rendered)

    def test_render_files(self):
        template.render_files_to_dir(values_file, template_files, output_dir)
        output = StringIO()

        def write(tfile, data):
            output.write(data)

        template.render_files(values_file, template_files, write)
        self.assertEqual(output.getvalue(), concat_tests())

    def test_render_files_to_stream(self):
        template.render_files_to_dir(values_file, template_files, output_dir)
        output = StringIO()
        template.render_files_to_stream(values_file, template_files, output)
        self.assertEqual(output.getvalue(), concat_tests())

    def test_render_files_to_file(self):
        clear_output_dir()
        template.render_files_to_file(values_file, template_files, test_file)
        self.assertTrue(os.path.isfile(test_file))

    def test_render_files_to_dir(self):
        clear_output_dir()
        template.render_files_to_dir(values_file, template_files, output_dir)
        self.assertTrue(os.path.isfile(test1_file))
        self.assertTrue(os.path.isfile(test2_file))

