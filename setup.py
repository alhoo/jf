#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
  name='pyq',
  description='Python json query engine',
  author='Lasse Hyyrynen',
  author_email='leh@protonmail.com',
  maintainer='Lasse Hyyrynen',
  maintainer_email='leh@protonmail.com',
  packages=find_packages(where='.'),
  setup_requires=[
    'setuptools>=20.2.2'
  ],
  install_requires=[
    'pygments>=2.0.0',
    'regex>=2016.3.2',
    'python-dateutil>=2.6.1',
    'PyYAML>=3.12',
    'dateparser>=0.6.0'
  ],
  tests_require=[
    'nose>=1.3.0'
  ],
  test_suite='tests',
  zip_safe=True,
  entry_points={
    'console_scripts': ['pyq=pyq.__main__:main']
  }
  )

