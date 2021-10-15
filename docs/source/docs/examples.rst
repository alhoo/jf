.. _examples:

Examples
========

This page contains examples on how to use JF.


Basic usage
-----------

Filter selected fields

.. code-block:: bash

    $ cat samples.jsonl | jf '{id: x.id, subject: x.fields.subject}'
    {"id": "87086895", "subject": "Swedish children stories"}
    {"id": "87114792", "subject": "New Finnish storybooks"}
    ...

Filter selected items

.. code-block:: bash

    $ cat samples.jsonl | jf '{id: x.id, subject: x.fields.subject},
            (x.id == "87114792")'
    {"id": "87114792", "subject": "New Finnish storybooks"}
    ...


Filter selected values

.. code-block:: bash

    $ cat samples.jsonl | jf 'x.id'
    "87086895"
    "87114792"


Complex tranformations
----------------------

Filter items by age, update existing data and output yaml

.. code-block:: bash

    $ cat samples.jsonl | jf '{id: x.id, datetime: x["content-datetime"]},
            (age(x.datetime) > age("456 days")),
            {age: age(x.datetime), ...}' --output yaml
    age: 457 days, 4:07:54.932587
    datetime: '2016-10-29 10:55:42+03:00'
    id: '87086895'

Sort items by age and print their id, length and age

.. code-block:: bash

    $ cat samples.jsonl|jf '{age: age(x["content-datetime"]), ...},
            sorted(x.age),
            {id: .id, length: "%d" % len(.content), age: .age}' --output yaml
    - id: '14941692'
      length: '63'
      age: 184 days, 0:02:20.421829
    - id: '90332110'
      length: '191'
      age: 215 days, 22:15:46.403613
    ...

Filter items after a given datetime (test.json is a git commit history):

.. code-block:: bash

    $ jf '{age: age(.commit.author.date), ...},
          (date(.commit.author.date) > date("2018-01-30T17:00:00Z")),
          sorted(x.age, reverse=True), {sha: .sha, age: .age, date: .commit.author.date}' test.json 
    {
      "sha": "68fe662966c57443ae7bf6939017f8ffa4b182c2",
      "age": "2 days, 9:40:12.137919",
      "date": "2018-01-30T18:35:27Z"
    }
    {
      "sha": "d3211e1141d8b2bf480cbbebd376b57bae9d8bdf",
      "age": "2 days, 9:18:07.134418",
      "date": "2018-01-30T18:57:32Z"
    }
    {
      "sha": "f8ba0ba559e39611bc0b63f236a3e67085fe8b40",
      "age": "2 days, 8:50:09.129790",
      "date": "2018-01-30T19:25:30Z"
    }

Importing modules
-----------------
Import your own modules and hide fields:

.. code-block:: bash

    $ cat test.json|jf --import_from modules/ --import demomodule --output yaml '{id: x.sha, ...},
            demomodule.timestamppipe(),
            islice(3,5)'
    - Pipemod: was here at 2018-01-31 09:26:12.366465
      id: f5f879dd7303c35fa3712586af1e7df884a5b98b
      url: https://api.github.com/repos/alhoo/jf/commits/f5f879dd7303c35fa3712586af1e7df884a5b98b
    - Pipemod: was here at 2018-01-31 09:26:12.368438
      id: b393d09215efc4fc0382dd82ec3f38ae59a287e5
      url: https://api.github.com/repos/alhoo/jf/commits/b393d09215efc4fc0382dd82ec3f38ae59a287e5

Read yaml:

.. code-block:: bash

    $ cat test.yaml | jf --input yaml '{id: x.sha, age: age(x.commit.author.date), ...},
            (x.age < age("1 days"))' --output yaml
    - age: 0 days, 22:45:56.388477
      author:
        avatar_url: https://avatars1.githubusercontent.com/u/8501204?v=4
        events_url: https://api.github.com/users/hyyry/events{/privacy}
        followers_url: https://api.github.com/users/hyyry/followers
        ...




.. toctree::
   :maxdepth: 4


