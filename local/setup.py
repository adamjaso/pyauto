from os import path
from setuptools import setup, find_packages
from pyauto.local import __version__


with open(path.join(path.dirname(__file__), 'requirements.txt')) as f:
    reqs = [l for l in f.read().strip().split('\n') if not l.startswith('-')]

setup(
    name='pyauto.local',
    version=__version__,
    description='Helper functions for working with local files and templates',
    author='Adam Jaso',
    license=open('LICENSE').read(),
    long_description=open('README.md').read(),
    packages=find_packages(),
    install_requires=reqs,
)
