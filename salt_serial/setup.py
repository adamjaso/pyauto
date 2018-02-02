from os import path
from setuptools import setup, find_packages
from pyauto.salt_serial import __version__


dirname = path.realpath(path.dirname(__file__))
with open(path.join(dirname, 'requirements.txt')) as f:
    reqs = [l for l in f.read().strip().split('\n') if not l.startswith('-')]

readme = path.join(dirname, 'README.md')


setup(
    name='pyauto.salt_serial',
    version=__version__,
    description='A module that serializes a Salt states tree or pillar into a base-64 encoded blob.',
    author='Adam Jaso',
    license='GNU General Public License V2',
long_description=open(readme).read(),
    packages=find_packages(),
    install_requires=reqs,
    url='https://github.com/adamjaso/pyauto/tree/master/openvpn',
)
