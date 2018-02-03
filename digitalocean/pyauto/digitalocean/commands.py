from . import config


def get_remote_droplet(config, droplet_id):
    return config.digitalocean.get_droplet(droplet_id).get_droplet_remote()


def deploy_droplet_opts(config, droplet_id):
    return config.digitalocean.get_droplet(droplet_id).deploy_opts()


def deploy_droplet(config, droplet_id):
    return config.digitalocean.get_droplet(droplet_id).deploy()


def destroy_droplet(config, droplet_id):
    return config.digitalocean.get_droplet(droplet_id).destroy()

