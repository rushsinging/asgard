# -*- coding: utf-8 -*-
from setuptools import setup

with open('./requirements.txt', 'r') as f:
    install_requires = f.read()

setup(
    name='asgard',
    url='http://git.iguokr.com/yggdrasil/asgard',
    license='BSD',
    author='Jade',
    description='Asgard -- A deploy tool bases on k8s ,helm and chartmuseum.',
    version='0.0.2',
    py_modules=['asgard'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'asgard = asgard:asgard'
        ]
    }
)

