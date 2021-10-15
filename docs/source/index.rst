.. jf documentation master file, created by
   sphinx-quickstart on Mon May  6 13:15:08 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to jf's documentation!
==============================

.. _about:

JF, aka "jndex fingers" or more commonly "json filter pipeline", is a jq-clone written in python.
It supports evaluation of python one-liners, making it especially appealing for data scientists
who are used to working with python.

Getting started
---------------

To get started, install jf

.. code-block:: bash

    pip install jf

Basic usage
-----------

Filter selected fields

.. code-block:: bash

    $ cat samples.jsonl | jf '{id: x.id, subject: x.fields.subject}'
    {"id": "87086895", "subject": "Swedish children stories"}
    {"id": "87114792", "subject": "New Finnish storybooks"}


To really get started using JF, start with the :ref:`userguide`.

For examples onf how you might use JF with your own data, check out the :ref:`examples`.

For detailed information about specific JF components, consult the :ref:`modules`.


.. toctree::
   :glob:
   :hidden:

   docs/user_guide
   docs/modules
   docs/examples
   docs/more_examples


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
