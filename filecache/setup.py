from os import path
from setuptools import setup, find_packages
from pyauto.filecache import __version__


dirname = path.realpath(path.dirname(__file__))
with open(path.join(dirname, 'requirements.txt')) as f:
    reqs = [l for l in f.read().strip().split('\n') if not l.startswith('-')]

readme = path.join(dirname, 'README.md')


setup(
    name='pyauto.filecache',
    version=__version__,
    description='A simple module to download and cache files',
    author='Adam Jaso',
    license='GNU General Public License V2',
long_description=open(readme).read(),
    packages=find_packages(),
    install_requires=reqs,
    url='https://github.com/adamjaso/pyauto/tree/master/filecache',

)