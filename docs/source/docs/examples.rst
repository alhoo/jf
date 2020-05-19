.. _examples:

Examples
========

This page contains examples on how to use JF.


Basic usage
-----------

Filter selected fields

.. code-block:: bash

    $ cat samples.jsonl | jf 'map({id: x.id, subject: x.fields.subject})'
    {"id": "87086895", "subject": "Swedish children stories"}
    {"id": "87114792", "subject": "New Finnish storybooks"}

Filter selected items

.. code-block:: bash

    $ cat samples.jsonl | jf 'map({id: x.id, subject: x.fields.subject}),
            filter(x.id == "87114792")'
    {"id": "87114792", "subject": "New Finnish storybooks"}

Filter selected items with shortened syntax

.. code-block:: bash

    $ cat samples.jsonl | jf '{id: x.id, subject: x.fields.subject},
            (x.id == "87114792")'
    {"id": "87114792", "subject": "New Finnish storybooks"}

Filter selected values

.. code-block:: bash

    $ cat samples.jsonl | jf 'map(x.id)'
    "87086895"
    "87114792"


Complex tranformations
----------------------

Filter items by age (and output yaml)

.. code-block:: bash

    $ cat samples.jsonl | jf 'map({id: x.id, datetime: x["content-datetime"]}),
            filter(age(x.datetime) > age("456 days")),
            update({age: age(x.datetime)})' --indent=5 --yaml
    age: 457 days, 4:07:54.932587
    datetime: '2016-10-29 10:55:42+03:00'
    id: '87086895'

Sort items by age and print their id, length and age

.. code-block:: bash

    $ cat samples.jsonl|jf 'update({age: age(x["content-datetime"])}),
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

.. code-block:: bash

    $ jf 'update({age: age(.commit.author.date)}),
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

Importing modules
-----------------
Import your own modules and hide fields:

.. code-block:: bash

    $ cat test.json|jf --import_from modules/ --import demomodule --yaml 'update({id: x.sha}),
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

.. code-block:: bash

    $ cat test.yaml | jf --yamli 'update({id: x.sha, age: age(x.commit.author.date)}),
            filter(x.age < age("1 days"))' --indent=2 --yaml
    - age: 0 days, 22:45:56.388477
      author:
        avatar_url: https://avatars1.githubusercontent.com/u/8501204?v=4
        events_url: https://api.github.com/users/hyyry/events{/privacy}
        followers_url: https://api.github.com/users/hyyry/followers
        ...


Group duplicates (age is within the same hour):

.. code-block:: bash

    $ cat test.json|jf --import_from modules/ --import demomodule 'update({id: x.sha}),
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

.. code-block:: bash

    $ jf --import_from modules/ --import re --import demomodule --input skype.json 'yield_from(x.messages),
            update({from: x.from.split(":")[-1], mid: x.skypeeditedid if x.skypeeditedid else x.clientmessageid}),
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


ML features
-----------

JF is integrated with SKlearn for building fast prototype machine learning systems from your data. The machine learning tools are packaged into the ml-module.

Building a machine learning model from your dataset:

.. code-block:: bash

    $ jf 'head(5000),
          map([x.text, x.label]),
          ml.persistent_trainer("model.pkl",
             ml.make_pipeline(
                 ml.make_union(ml.CountVectorizer(),
                               ml.CountVectorizer(analyzer="char", ngram_range=(4,4))),
                 ml.LogisticRegression()))' dataset.jsonl.gz

In the above script we take the first 5000 samples, select the "text"-column as the model features and "status"-column as the classifier target. We use the sklearn `CountVectorizer` to build both word and character level features, which we pass to the logistic regression. The ml.persistent_trainer then takes your model and fits it using the jf transformation pipeline defined before the trainer. The trainer assumes you feed it with [sample, target]-pairs when fitting a supervised model.

To further serve your models, you can use the jf-service-module to build an API from your model:

.. code-block:: bash

    $ jf 'head(5000),
          map([x.text, x.status]),
          ml.persistent_trainer("model.pkl",
             ml.make_pipeline(
                 ml.make_union(ml.CountVectorizer(),
                               ml.CountVectorizer(analyzer="char", ngram_range=(4,4))),
                 ml.LogisticRegression())),
          service.RESTful("/predict")' dataset.jsonl.gz &
    
    $ curl --silent -X POST -d '["Donald Trump is a bit simple"]' localhost:5002/predict
    [ "TRUMP_RANT", [0.9532, 0.0468] ]

Using JF as a library
---------------------

JF can also be used as a library for building more persistent services. We have included an example of this under `examples/` in the git repository. The basic usage as illustrated below.

.. code-block:: python3

    # examples/example0.py

    from pprint import pprint
    import jf
    from jf.process import Map, Col, Pipeline

    # Define the x that represents one sample in your dataset
    x = Col()

    dataset = jf.input.read_file("dataset.jsonl.gz")

    # Use the x as you would use it in your command lines
    transformations = [Map(dict(id=x.id, energy=x.energy))]

    transformed_dataset = jf.process.Pipeline(transformations).transform(dataset)
    pprint(transformed_dataset)

.. toctree::
   :maxdepth: 4


