import digitalocean
from pyauto.local import config as local_config
from pyauto.core import config


class Digitalocean(config.Config):
    def __init__(self, *args, **kwargs):
        super(Digitalocean, self).__init__(*args, **kwargs)
        self['droplets'] = [Droplet(d, self) for d in self['droplets']]

    def get_droplet(self, droplet_id):
        for d in self['droplets']:
            if droplet_id == d['id']:
                return d
        return None

    def get_droplet_profile(self, profile_id):
        return self['droplet_profiles'].get(profile_id, {})

    def get_droplet_client(self, **kwargs):
        return digitalocean.Droplet(token=self['token'], **kwargs)

    def get_manager_client(self, **kwargs):
        return digitalocean.Manager(token=self['token'], **kwargs)


class Droplet(dict):
    def __init__(self, d, config):
        super(Droplet, self).__init__(d)
        self.config = config

    @property
    def droplet_tag(self):
        return ':'.join(['droplet_name', self.droplet_name])

    @property
    def droplet_profile(self):
        return self.config.get_droplet_profile(self['profile'])

    @property
    def droplet_name(self):
        return '-'.join([self['name'], self.droplet_profile['size'], self['region']])

    def get_droplet_remote(self):
        ds = self.config.get_manager_client().get_all_droplets(tag_name=self.droplet_tag)
        if not ds:
            return None
        return ds[0]

    def destroy(self):
        return self.get_droplet_remote().destroy()

    def get_deploy_opts(self, **kwargs):
        create_opts = {}
        profile = self.config.get_droplet_profile(self['profile'])
        create_opts.update(profile)
        create_opts.update(kwargs)
        create_opts['name'] = self.droplet_name
        create_opts['region'] = self['region']
        create_opts['tags'] = [self.droplet_tag]
        return create_opts

    def deploy(self, **kwargs):
        opts = self.get_deploy_opts(**kwargs)
        droplet = self.get_droplet_remote()
        if not droplet:
            create_opts = self.get_deploy_opts(**kwargs)
            droplet = self.config.get_droplet_client()
            droplet.create(**create_opts)
            actions = droplet.get_events()
            while len(actions) and 'completed' != actions[0].status:
                actions = droplet.get_events()
            droplet.load()
        return droplet


config.set_config_class('digitalocean', Digitalocean)
