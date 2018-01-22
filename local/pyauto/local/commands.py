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
