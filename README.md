[![Build Status](https://travis-ci.org/alhoo/jf.svg?branch=master)](https://travis-ci.org/alhoo/jf)
[![Coverage](https://codecov.io/github/alhoo/jf/coverage.svg?branch=master)](https://codecov.io/github/alhoo/jf)
[![PyPI](https://img.shields.io/pypi/v/jf.svg)](https://pypi.python.org/pypi/jf)

JF
==

JF, aka "jndex fingers" or more commonly "json filter pipeline", is a jq-clone written in python.
It supports evaluation of python oneliners, making it especially appealing for data scientists
who are used to working with python.


How does it work
==

JF works by converting streaming json or yaml data structure through a map/filter-pipeline.
The pipeline is compiled from a string representing a comma-separated list filters and mappers.
The query parser assumes that each function of the pipeline reads items from a generator.
The generator is given as the last non-keyword parameter to the function, 
so "map(conversion)" is interpreted as "map(conversion, inputgenerator)".
The result from a previous function is given as the input generator for the next function in the pipeline.

Some built-in functions headers have been remodeled to be more intuitive with the framework.
Most noticeable is the sorted-function, which normally has the key defined as a keyword argument.
This was done since it seems more logical to sort items by id by writing "sorted(x.id)" than "sorted(key=lambda x: x.id)".
Similar changes are done for some other useful functions:

* islice(stop) => islice(arr, start=0, stop, step=1)
* islice(start, stop, step=1) => islice(arr, start, stop, step)
* first(N=1) => islice(N)
* last(N=1) => list(arr)[-N:]
* I = arr (== identity operation)
* yield\_from(x) => yield items from x
* chain() => combine items into a list

For datetime processing, two useful helper functions are imported by default:

* date(string) for parsing string into a python datetime-object
* age(string) for calculating timedelta between now() and date(string)

These are useful for sorting or filtering items in based on timestamps.

For shortened syntax, '{...}' is interpreted as 'map({...})' and (...) is interpreted as filter(...).


Basic usage
==

Filter selected fields

    $ cat samples.jsonl | jf 'map({id: x.id, subject: x.fields.subject})'
    {"id": "87086895", "subject": "Swedish children stories"}
    {"id": "87114792", "subject": "New Finnish storybooks"}

Filter selected items

    $ cat samples.jsonl | jf 'map({id: x.id, subject: x.fields.subject}),
            filter(x.id == "87114792")'
    {"id": "87114792", "subject": "New Finnish storybooks"}

Filter selected items with shortened syntax

    $ cat samples.jsonl | jf '{id: x.id, subject: x.fields.subject},
            (x.id == "87114792")'
    {"id": "87114792", "subject": "New Finnish storybooks"}

Filter selected values

    $ cat samples.jsonl | jf 'map(x.id)'
    "87086895"
    "87114792"


Filter items by age (and output yaml)

    $ cat samples.jsonl | jf 'map({id: x.id, datetime: x["content-datetime"]}),
            filter(age(x.datetime) > age("456 days")),
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

Filter items after a given datetime (test.json is a git commit history):

    $ jf 'map(.update({age: age(.commit.author.date)})),
            filter(date(.commit.author.date) > date("2018-01-30T17:00:00Z")),
            sorted(x.age, reverse=True), map(.sha, .age, .commit.author.date)' test.json 
    [
      "68fe662966c57443ae7bf6939017f8ffa4b182c2",
      "2 days, 9:40:12.137919",
      "2018-01-30T18:35:27Z"
    ]
    [
      "d3211e1141d8b2bf480cbbebd376b57bae9d8bdf",
      "2 days, 9:18:07.134418",
      "2018-01-30T18:57:32Z"
    ]
    [
      "f8ba0ba559e39611bc0b63f236a3e67085fe8b40",
      "2 days, 8:50:09.129790",
      "2018-01-30T19:25:30Z"
    ]

Import your own modules and hide fields:

    $ cat test.json|jf --import demomodule --yaml 'map(x.update({id: x.sha})),
            demomodule.timestamppipe(),
            hide("sha", "committer", "parents", "html_url", "author", "commit",
                 "comments_url"), islice(3,5)'
    - Pipemod: was here at 2018-01-31 09:26:12.366465
      id: f5f879dd7303c35fa3712586af1e7df884a5b98b
      url: https://api.github.com/repos/alhoo/jf/commits/f5f879dd7303c35fa3712586af1e7df884a5b98b
    - Pipemod: was here at 2018-01-31 09:26:12.368438
      id: b393d09215efc4fc0382dd82ec3f38ae59a287e5
      url: https://api.github.com/repos/alhoo/jf/commits/b393d09215efc4fc0382dd82ec3f38ae59a287e5

Read yaml:

    $ cat test.yaml | jf --yamli 'map(x.update({id: x.sha, age: age(x.commit.author.date)})),
            filter(x.age < age("1 days"))' --indent=2 --yaml
    - age: 0 days, 22:45:56.388477
      author:
        avatar_url: https://avatars1.githubusercontent.com/u/8501204?v=4
        events_url: https://api.github.com/users/hyyry/events{/privacy}
        followers_url: https://api.github.com/users/hyyry/followers
        ...


Group duplicates (age is within the same hour):

    $ cat test.json|jf --import demomodule 'map(x.update({id: x.sha})),
            sorted(.commit.author.date, reverse=True),
            demomodule.DuplicateRemover(int(age(.commit.author.date).total_seconds()/3600),
            group=1).process(lambda x: {"duplicate": x.id}),
            map(list(map(lambda y: {age: age(y.commit.author.date), id: y.id, 
                         date: y.commit.author.date, duplicate_of: y["duplicate"],
                         comment: y.commit.message}, x))),
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

Use pythonic conditional operation, string.split() and complex string and date formatting with built-in python syntax. Also you can combine the power of regular expressions by including the re-library.

    $ jf --import re --import demomodule --input skype.json 'yield_from(x.messages),
            map(x.update({from: x.from.split(":")[-1], mid: x.skypeeditedid if x.skypeeditedid else x.clientmessageid})),
            sorted(age(x.composetime), reverse=True),
            demomodule.DuplicateRemover(x.mid, group=1).process(),
            map(last(x)),
            yield_from(x),
            sorted(age(.composetime), reverse=True),
            map("%s %s: %s" % (date(x.composetime).strftime("%d.%m.%Y %H:%M"), x.from, re.sub(r"(<[^>]+>)+", " ", x.content)))' --raw
    27.01.2018 11:02 2296ead9324b68aef4bc105c8e90200c@thread.skype:  1518001760666 8:live:matti_3426 8:live:matti_6656 8:hyyrynen.london 8:live:suvi_56 8:jukka.mattinen 
    27.01.2018 11:12 matti_7626: Required competence: PHP programmer (Mika D, Markus H, Heidi), some JavaScript (e.g. for GUI)
    27.01.2018 11:12 matti_7626: Matti: parameters part
    27.01.2018 11:15 matti_7626: 1.) Clarify customer requirements - AP: Suvi/Joseph
    27.01.2018 11:22 matti_7626: This week - initial installation and setup
    27.01.2018 11:22 matti_7626: Next week (pending customer requirements) - system configuration
    27.01.2018 11:25 matti_7626: configuration = parameters, configuration files (audio files, from customer, ask Suvi to request today?), add audio files to system (via GUI)
    27.01.2018 11:26 matti_7626: Testing = specify how we do testing, for example written test cases by the customer.
    27.01.2018 11:28 matti_7626: Need test group (testgroup 1 prob easiest to recognise says Lasse)






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
* Drop your filtered data to IPython for manual data exploration

Known bugs
==

* IPython doesn't launch perfectly with piped data
