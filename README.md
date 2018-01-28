pyq
==

pyq is a jq-clone written in python. It supports evaluation of python oneliners, which makes it
especially appealing for data scientists who are used to python.

Basic usage
==

* filter selected fields

    cat samples.jsonl | pyq '{id: x.id, subject: x.fields.subject}'

* filter selected values

    cat samples.jsonl | pyq 'id: x.id'
