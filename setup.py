from setuptools import setup
from pyauto import __version__


setup(
    name='pyauto',
    version=__version__,
    description='PyAuto Core',
    author='Adam Jaso',
    packages=['pyauto'],
    package_dir={'pyauto': 'pyauto'},
    install_requires=['PyYAML', 'six'],
    url='https://github.com/adamjaso/pyauto',
)
