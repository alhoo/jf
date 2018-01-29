pyq
==

pyq is a jq-clone written in python. It supports evaluation of python oneliners, which makes it
especially appealing for data scientists who are used to python.

Basic usage
==

filter selected fields

    $ cat samples.jsonl | pyq 'map({id: x.id, subject: x.fields.subject})'
    {"id": "87086895", "subject": "Swedish children stories"}
    {"id": "87114792", "subject": "New Finnish storybooks"}

filter selected items

    $ cat samples.jsonl | pyq 'map({id: x.id, subject: x.fields.subject}), filter(x.id == "87114792")'
    {"id": "87114792", "subject": "New Finnish storybooks"}

filter selected values

    $ cat samples.jsonl | pyq 'map(x.id)'
    "87086895"
    "87114792"

filter items by age (and output yaml)

    $ cat samples.jsonl | pyq 'map({id: x.id, datetime: x["content-datetime"]}), filter(age(x.datetime) > age("456 days")), map(.update({age: age(x.datetime)}))' --indent=5 --yaml
    age: 457 days, 4:07:54.932587
    datetime: '2016-10-29 10:55:42+03:00'
    id: '87086895'


Installing
==

    pip install git+https://github.com/alhoo/pyq


Known bugs
==

* Does not support all json formats (ex. jq . sample.jsonl|pyq '')
* Datetime-recognition is crude and will probably make mistakes

