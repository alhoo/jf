[![Build Status](https://travis-ci.org/alhoo/jf.svg?branch=master)](https://travis-ci.org/alhoo/jf)
[![Coverage](https://codecov.io/github/alhoo/jf/coverage.svg?branch=master)](https://codecov.io/github/alhoo/jf)
[![PyPI](https://img.shields.io/pypi/v/jf.svg)](https://pypi.python.org/pypi/jf)
[![Documentation Status](https://readthedocs.org/projects/jf/badge/?version=latest)](https://jf.readthedocs.io/en/latest/?badge=latest)

JF
==

JF, aka "jndex fingers" or more commonly "json filter pipeline", is a jq-clone written in python.
It supports evaluation of python one-liners, making it especially appealing for data scientists
who are used to working with python.


Installing
==

    pip install jf


Features
==

supported formats:
* json (uncompressed, gzip, bz2)
* jsonl (uncompressed, gzip, bz2)
* yaml (uncompressed, gzip, bz2)
* csv and xlsx support if pandas and xlrd is installed
* markdown table output support
* xlsx (excel)
* parquet

transformations:
* construct generator pipeline with map, hide, filter
* access json dict as classes with dot-notation for attributes
* datetime and timedelta comparison
  * age() for timedelta between datetime and current time
* first(N), last(N), islice(start, stop, step)
  * head and tail alias for last and first
* firstnlast(N) (or headntail(N))
* import your own modules for more complex filtering
  * Support stateful classes for complex interactions between items
* drop your filtered data to IPython for manual data exploration
* pandas profiling support for quick data exploration
* use --ordered\_dict to keep items in order
* sklearn toolbox for machine learning
* running restful service for the transformation pipeline

Known bugs
==

* IPython doesn't launch perfectly with piped data
