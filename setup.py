#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
  name = 'pyq',
  packages = ['pyq'],
  version = '0.1',
  description = 'Python jsonl query engine',
  author = 'Lasse Hyyrynen',
  author_email = 'leh@protonmail.com',
  maintainer = 'Lasse Hyyrynen',
  maintainer_email = 'leh@protonmail.com',
  keywords = ['json', 'yaml', 'jq'],
  download_url = 'https://github.com/alhoo/pyq/archive/0.1.tar.gz',
  url = 'https://github.com/alhoo/pyq',
  setup_requires = [
    'setuptools_scm> = 1.10.1',
    'setuptools> = 20.2.2'
  ],
  install_requires = [
  ],
  tests_require = [
    'nose> = 1.3.0'
  ],
  test_suite = 'tests',
  zip_safe = True,
  entry_points = {
    'console_scripts': ['pyq = pyq.__main__:main']
  }
)

