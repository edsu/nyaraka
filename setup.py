version = '0.0.4'

from setuptools import setup

setup(
    name = 'nyaraka',
    version = version,
    url = 'http://github.com/edsu/nyaraka',
    author = 'Ed Summers',
    author_email = 'ehs@pobox.com',
    py_modules = ['nyaraka',],
    scripts = ['nyaraka.py',],
    install_requires = ['requests', 'tqdm'],
    description = 'Download Omeka data',
)
