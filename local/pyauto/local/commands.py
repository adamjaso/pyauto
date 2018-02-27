import json
import yaml
from . import config


def init_workspace(config):
    config.local.init_workspace()


def render(config, template_filename, args_filename):
    args_filename = config.local.get_template_file(args_filename)
    with open(args_filename) as f:
        kwargs = yaml.load(f)
        return config.local.render_template(template_filename, **kwargs)


def src_dst_copytree(config, src_id, dest_id):
    return config.local.copytree(src_id, dest_id)


def dst_copytree(config, dst_id):
    return config.local.get_destination(dst_id).copytree()


def dst_rmtree(config, dst_id):
    return config.local.get_destination(dst_id).rmtree()


def dst_get_template_destinations(config, dst_id):
    return config.local.get_destination(dst_id).get_template_destinations()


def dst_render_templates(config, dst_id):
    return config.local.get_destination(dst_id).render_templates()


def dst_render_template(config, dst_id, template_id):
    return config.local.get_destination(dst_id)\
                       .get_template(template_id).render_template()


def dst_get_context(config, dst_id, template_id):
    data = config.local.get_destination(dst_id)\
                       .get_template(template_id).get_context()
    return json.dumps(data, indent=2)


def template_get_context(config, template_id):
    data = config.local.get_template(template_id).get_context()
    return json.dumps(data, indent=2)
