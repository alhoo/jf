#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
  name='pyq',
  description='Python json query engine',
  author='Lasse Hyyrynen',
  author_email='leh@protonmail.com',
  maintainer='Lasse Hyyrynen',
  maintainer_email='leh@protonmail.com',
  setup_requires=[
    'setuptools_scm>=1.10.1',
    'setuptools>=20.2.2'
  ],
  install_requires=[
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

