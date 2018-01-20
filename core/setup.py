from os import path
from setuptools import setup
from pyauto.core import __version__


dirname = path.realpath(path.dirname(__file__))
with open(path.join(dirname, 'requirements.txt')) as f:
    reqs = [l for l in f.read().strip().split('\n') if not l.startswith('-')]

license = path.join(dirname, 'LICENSE')
readme = path.join(dirname, 'README.md')

setup(
    name='pyauto',
    author='Adam Jaso',
    version=__version__,
    description='PyAuto Core',
    license=open(license).read(),
    long_description=open(readme).read(),
    packages=['pyauto.core'],
    package_dir={'pyauto.core': 'pyauto/core'},
    install_requires=reqs,
    url='https://github.com/adamjaso/pyauto',
)
