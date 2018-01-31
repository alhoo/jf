jf
==

jf, aka json filter pipeline, is a jq-clone written in python. It supports evaluation of python oneliners, making it
especially appealing for data scientists who are used to python.

Basic usage
==

Filter selected fields

    $ cat samples.jsonl | jf 'map({id: x.id, subject: x.fields.subject})'
    {"id": "87086895", "subject": "Swedish children stories"}
    {"id": "87114792", "subject": "New Finnish storybooks"}

Filter selected items

    $ cat samples.jsonl | jf 'map({id: x.id, subject: x.fields.subject}), filter(x.id == "87114792")'
    {"id": "87114792", "subject": "New Finnish storybooks"}

Filter selected values

    $ cat samples.jsonl | jf 'map(x.id)'
    "87086895"
    "87114792"

Filter items by age (and output yaml)

    $ cat samples.jsonl | jf 'map({id: x.id, datetime: x["content-datetime"]}), filter(age(x.datetime) > age("456 days")),
            map(.update({age: age(x.datetime)}))' --indent=5 --yaml
    age: 457 days, 4:07:54.932587
    datetime: '2016-10-29 10:55:42+03:00'
    id: '87086895'

Sort items by age and print their id, length and age

    $ cat samples.jsonl|jf 'map(x.update({age: age(x["content-datetime"])})),
            sorted(x.age),
            map(.id, "length: %d" % len(.content), .age)' --indent=3 --yaml
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

Import your own modules and hide fields:

    $ cat test.json|jf --import demomodule --yaml 'map(x.update({id: x.sha})),
            demomodule.timestamppipe(),
            hide("sha", "committer", "parents", "html_url", "author", "commit", "comments_url"),
            islice(3,5)'
    - Pipemod: was here at 2018-01-31 09:26:12.366465
      id: f5f879dd7303c35fa3712586af1e7df884a5b98b
      url: https://api.github.com/repos/alhoo/jf/commits/f5f879dd7303c35fa3712586af1e7df884a5b98b
    - Pipemod: was here at 2018-01-31 09:26:12.368438
      id: b393d09215efc4fc0382dd82ec3f38ae59a287e5
      url: https://api.github.com/repos/alhoo/jf/commits/b393d09215efc4fc0382dd82ec3f38ae59a287e5

Read yaml:

    $ cat test.yaml | jf --yamli 'map(x.update({id: x.sha, age: age(x.commit.author.date)})),
            filter(x.age < age("1 days"))' --indent=2 --yaml

Group duplicates (age is within the same hour):

    $ cat test.json|jf --import demomodule 'map(x.update({id: x.sha})),
            sorted(.commit.author.date, reverse=True),
            demomodule.DuplicateRemover(int(age(.commit.author.date).total_seconds()/3600),
            group=1).process(lambda x: {"duplicate": x.id}),
            map(list(map(lambda y: {age: age(y.commit.author.date),
            id: y.id, date: y.commit.author.date, duplicate_of: y["duplicate"], comment: y.commit.message}, x))),
            first(2)'
    [
      {
        "comment": "Add support for hiding fields",
        "duplicate_of": null,
        "id": "f8ba0ba559e39611bc0b63f236a3e67085fe8b40",
        "age": "16:19:00.102299",
        "date": "2018-01-30 19:25:30+00:00"
      },
      {
        "comment": "Enhance error handling",
        "duplicate_of": "f8ba0ba559e39611bc0b63f236a3e67085fe8b40",
        "id": "d3211e1141d8b2bf480cbbebd376b57bae9d8bdf",
        "age": "16:46:58.104188",
        "date": "2018-01-30 18:57:32+00:00"
      }
    ]
    [
      {
        "comment": "Reduce verbosity when debugging",
        "duplicate_of": null,
        "id": "f5f879dd7303c35fa3712586af1e7df884a5b98b",
        "age": "19:26:00.106777",
        "date": "2018-01-30 16:18:30+00:00"
      },
      {
        "comment": "Print help if no input is given",
        "duplicate_of": "f5f879dd7303c35fa3712586af1e7df884a5b98b",
        "id": "b393d09215efc4fc0382dd82ec3f38ae59a287e5",
        "age": "19:35:16.108654",
        "date": "2018-01-30 16:09:14+00:00"
      }
    ]






Installing
==

    pip install jf


Features
==

* json, jsonl and yaml files for input and output
* construct generator pipeline with map, hide, filter
* access json dict as classes with dot-notation for attributes
* datetime and timedelta comparison
  * age() for timedelta between datetime and current time
* first(N), last(N), islice(start, stop, step)
* import your own modules for more complex filtering
  * Support stateful classes for complex interactions between items

Known bugs
==

* Datetime-recognition is crude and will probably make mistakes

