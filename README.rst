|Build Status| |Coverage| |PyPI| |Documentation Status|

JF
==

JF, aka “jndex fingers” or more commonly “json filter pipeline”, is a
jq-clone written in python. It supports evaluation of python one-liners,
making it especially appealing for data scientists who are used to
working with python.

Installing
==========

::

   pip install jf

Basic usage
===========

Filter selected fields

::

   $ cat samples.jsonl | jf '{id: x.id, subject: x.fields.subject}'
   {"id": "87086895", "subject": "Swedish children stories"}
   {"id": "87114792", "subject": "New Finnish storybooks"}
   ...

Features
========

supported formats:

-  json (uncompressed, gzip, bz2)
-  jsonl (uncompressed, gzip, bz2)
-  yaml (uncompressed, gzip, bz2)
-  csv and xlsx support if pandas and openpyxl is installed
-  markdown table output support
-  xlsx (excel)
-  parquet

transformations:

-  import and use python modules with –import
-  import additional json for merging and joining using –import
   name=filename.json
-  initialize transformations with –init
-  access json dict as classes with dot-notation for attributes
-  datetime and timedelta comparison

   -  age() for timedelta between datetime and current time

-  first(N), last(N), islice(start, stop, step)

   -  head and tail alias for last and first

-  firstnlast(N) (or headntail(N))
-  import your own modules for more complex filtering and
   transformations

   -  Support stateful classes for complex interactions between items

-  sklearn toolbox for machine learning
-  running restful service for the transformation pipeline

.. |Build Status| image:: https://api.travis-ci.com/alhoo/jf.svg?branch=master
   :target: https://travis-ci.com/alhoo/jf
.. |Coverage| image:: https://codecov.io/github/alhoo/jf/coverage.svg?branch=master
   :target: https://codecov.io/github/alhoo/jf
.. |PyPI| image:: https://img.shields.io/pypi/v/jf.svg
   :target: https://pypi.python.org/pypi/jf
.. |Documentation Status| image:: https://readthedocs.org/projects/jf/badge/?version=latest
   :target: https://jf.readthedocs.io/en/latest/?badge=latest
