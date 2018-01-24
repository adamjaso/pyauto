from os import path
from setuptools import setup, find_packages
from pyauto.ouidb import __version__


dirname = path.realpath(path.dirname(__file__))
with open(path.join(dirname, 'requirements.txt')) as f:
    reqs = [l for l in f.read().strip().split('\n') if not l.startswith('-')]

license = path.join(dirname, 'LICENSE')
readme = path.join(dirname, 'README.md')

setup(
    name='pyauto.ouidb',
    version=__version__,
    description='Builds a database from the OUI MAC vendors',
    author='Adam Jaso',
    license=open(license).read(),
    long_description=open(readme).read(),
    packages=find_packages(),
    install_requires=reqs,
    url='https://github.com/adamjaso/pyauto',
)
