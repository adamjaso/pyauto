class Droplet(object):
    def __init__(self, droplet_obj):
        self.raw = droplet_obj

    def get_ipv4_address(self, network_type):
        for ip in self.raw.networks['v4']:
            if network_type == ip['type']:
                return ip
        raise Exception('IPv4 addresses not found')

    @property
    def public_ip(self):
        return self.get_ipv4_address('public').get('ip_address')
