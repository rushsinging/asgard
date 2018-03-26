# -*- coding: utf-8 -*-
from setuptools import setup

with open('./requirements.txt', 'r') as f:
    install_requires = f.read()

setup(
    name='asgard',
    version='0.0.1',
    py_modules=['asgard'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'asgard = asgard:asgard'
        ]
    }
)

