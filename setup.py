# -*- coding: utf-8 -*-
import os

from setuptools import setup

path = os.path.dirname(os.path.abspath(__file__))
# with open(os.path.join(path, 'requirements.txt'), 'r') as f:
with open('requirements.txt', 'r') as f:
    install_requires = f.read()

print(install_requires)

setup(
    name='asgard',
    url='http://git.iguokr.com/yggdrasil/asgard',
    license='BSD',
    author='Jade',
    description='Asgard -- A deploy tool bases on k8s ,helm and chartmuseum.',
    version='0.0.12',
    zip_safe=False,
    include_package_data=True,
    py_modules=['asgard'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'asgard = asgard:asgard'
        ]
    }
)
