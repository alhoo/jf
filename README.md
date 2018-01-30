pyq
==

pyq, aka πq, is a jq-clone written in python. It supports evaluation of python oneliners, making it
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

Sort items by age and print their id, length and age

    $ cat test.jsonl|pyq 'map(x.update({age: age(x["content-datetime"])})), sorted(x.age), map(.id, "length: %d" % len(.content), .age)' --indent=3 --yaml
    - '14941692'
    - 'length: 63'
    - 184 days, 0:02:20.421829
    - '90332110'
    - 'length: 191'
    - 215 days, 22:15:46.403613
    - '88773908'
    - 'length: 80'
    - 350 days, 3:11:06.412088
    - '14558799'
    - 'length: 1228'
    - 450 days, 6:30:54.419461
    - '87182405'
    - 'length: 251'



Installing
==

    pip install git+https://github.com/alhoo/pyq


Known bugs
==

* Does not support all json formats (ex. jq . sample.jsonl|pyq '')
* Datetime-recognition is crude and will probably make mistakes

