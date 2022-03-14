#!/usr/bin/env python

from os import path
from codecs import open
from setuptools import find_packages, setup, Extension

here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

version = "1.1.1"

setup(
    name="jf",
    version=version,
    description="Python jsonl query engine",
    long_description=long_description,
    author="Lasse Hyyrynen",
    author_email="lasse.hyyrynen@pm.me",
    maintainer="Lasse Hyyrynen",
    maintainer_email="lasse.hyyrynen@pm.me",
    license="MIT",
    keywords=["json", "jsonl", "yaml", "jq"],
    download_url="https://github.com/alhoo/jf/archive/%s.tar.gz" % version,
    url="https://github.com/alhoo/jf",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Utilities",
    ],
    packages=["jf"],
    setup_requires=["setuptools>=20.2.2"],
    ext_modules=[
        Extension(
            "jf.jsonlgen",
            sources=["jf/jsonlgen.cc"],
            language='c++',
            extra_compile_args="-std=c++11 -O3 -funroll-loops -march=native".split(),
        ),
    ],
    install_requires=[
        "pygments>=2.4.0",
        "regex>=2016.3.2",
        "python-dateutil>=2.4.1",
        "ruamel.yaml>=0.16.10",
        "dateparser>=0.6.0",
        "pandas>=0.22.0",
        "Click>=7.0.0",
    ],
    tests_require=[
        "nose>=1.3.0",
        "pandas>=0.22.0",
        "openpyxl>=2.5.4",
        "pylint>=1.8.2",
        "pytest",
        "pytest-coverage",
        "pytest-flake8",
    ],
    extras_require={"dev": ["recommonmark", "sphinx", "sphinx-rtd-theme"]},
    test_suite="tests",
    zip_safe=True,
    entry_points={"console_scripts": ["jf=jf.__main__:main"]},
)
