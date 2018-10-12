import os
import re

from setuptools import setup, find_packages


def get_version():
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, 'peewee_filters', '__init__.py')) as f:
        return re.findall(r"^__version__ = '([^']+)'\r?$", f.read(), re.M)[0]


setup(
    name='peewee_filters',
    version=get_version(),
    description='Generating peewee query expression against json payload.',
    url='https://github.com/wonderbeyond/peewee_filters',
    author='wonderbeyond',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=[
        'six',
        'peewee>=3.4.0',
    ],
    zip_safe=False,
)
