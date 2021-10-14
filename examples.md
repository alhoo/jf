## Basics

Selecting is done with `{key: value}`:

```bash
 $ head -n 1000 /media/lasse/853bf813-fe58-4786-9d4a-186d28bf36fe/Data/reddit/datascience_10.jsonl|jf '{body: .body}' -c 
{"body": "This is an excellent cautionary tale regarding internships.\n\nA company that doesn't have sufficient time or manpower to train interns in business essential processes and due to laws regarding internships can't make interns responsible for business essential processes. Make sure you are getting the right internship by asking how much time they have to give to you and not just what you can agree to do for them in exchange for an internship on a resume."}
{"body": "Learn how to sex up your resume. That's what everyone else does."}
{"body": "Was I the one swearing my head off... Nope and I definitely was not referring to you when I said that comment."}
{"body": "[deleted]"}
...
```

Updating is done with the [spread notation similarly as in javascript object literals](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Spread_syntax#spread_in_object_literals)  `{key: value, ...}`

```bash
 $ echo '{"text": "Hello world. How are you doing today?"}' | jf '{length: len(.text), ...}'
{
  "text": "Hello world. How are you doing today?",
  "length": 37
}
```

Filtering with the `(condition)` notation

```bash
 $ cat dataset.jsonl|jf '{body: .body}, (len(.body) < 10)' -c
{"body": "[deleted]"}
{"body": "No."}
{"body": "[deleted]"}
{"body": "[deleted]"}
{"body": "[deleted]"}
...
```

### JF Script

JF commands can be conveniently written to scripts

```bash
#!/usr/bin/env jf
{body: .body}, (len(.body) < 10)
```

and run as:

```bash
 $ cat dataset.jsonl| ./script.jf -c
{"body": "[deleted]"}
{"body": "No."}
{"body": "[deleted]"}
{"body": "[deleted]"}
{"body": "[deleted]"}
...
```

## Complex

JF supports a list of powerful additions.

## Import

Import python libraries for access to more functions

```bash
 $ cat dataset.jsonl|jf '{body: .body, hash: hashlib.md5(.body.encode()).hexdigest()}, first(10)' -c --import hashlib
{"body": "This is an excellent cautionary tale regarding internships.\n\nA company that doesn't have sufficient time or manpower to train interns in business essential processes and due to laws regarding internships can't make interns responsible for business essential processes. Make sure you are getting the right internship by asking how much time they have to give to you and not just what you can agree to do for them in exchange for an internship on a resume.", "hash": "061bbff82a643a499e245776aadd5dbe"}
{"body": "Learn how to sex up your resume. That's what everyone else does.", "hash": "5eb30479571d988b85754952aae466a4"}
{"body": "Was I the one swearing my head off... Nope and I definitely was not referring to you when I said that comment.", "hash": "06337fbd31ec80697339dbfff36fb481"}
{"body": "[deleted]", "hash": "3e4ce20ec588600054f050310750c4ca"}
...
```

As a script:

```bash
 $ cat hashlib.jf 
#!/usr/bin/env jf
#import hashlib

{body: .body, hash: hashlib.md5(.body.encode()).hexdigest()}, first(10)
```

```bash
 $ cat dataset2.jsonl|./hashlib.jf -c
{"body": "Maybe talk to her about it, give her a warning aboit how this will go down if she doesnt change. ", "hash": "1b1948d36dc415e97b31a53c89db0d79"}
{"body": "First off—are you completely and totally super sure she’s ACTUALLY flirting with you and not just being herself?\n\nIf you are sure, make sure she knows you’re not interested and value your friendship gently yet firmly.", "hash": "5b9e6d64c9bf0174a18784e253c67940"}
{"body": "Ah, one of those cases where you add 20 years to your age", "hash": "38accd597fa3b069841eb86db33ed20f"}
```

### Init

Use initialization for complex transformation

```bash
 $ echo '{"text": "Hello world. How are you doing today?"}' \
     | jf --import spacy \
            --init 'nlp = spacy.load("en_core_web_sm")' \
            '{text: " ".join(["/".join([str(token), token.pos_])
              if token.pos_ in ("NOUN", ) else str(token)
              for token in nlp(.text)])}'             
{
  "text": "Hello world/NOUN . How are you doing today/NOUN ?"
}
```

As a script scripts:

```bash
#!/usr/bin/env jf
#import spacy
#init nlp = spacy.load("en_core_web_sm")

{text: " ".join(["/".join([str(token), token.pos_])
              if token.pos_ in ("NOUN", ) else str(token)
              for token in nlp(.text)])}
```

### Multiprocessing

With a larger dataset, using `--processes <num processes>` can significantly increase the speed of processing when using heavy functions.

```zsh
 $ time head -n 1000 dataset.jsonl|jf --import spacy --init 'nlp = spacy.load("en_core_web_sm")' '{text: " ".join(["/".join([str(token), token.pos_]) if token.pos_ in ("NOUN", ) else str(token) for token in nlp(.body)]), ...}' >/dev/null
head -n 1000   0,01s user 0,00s system 0% cpu 15,751 total
jf --import spacy --init 'nlp = spacy.load("en_core_web_sm")'  >   16,62s user 0,16s system 100% cpu 16,669 total

$ time head -n 1000 dataset.jsonl|jf --import spacy --init 'nlp = spacy.load("en_core_web_sm")' '{text: " ".join(["/".join([str(token), token.pos_]) if token.pos_ in ("NOUN", ) else str(token) for token in nlp(.body)]), ...}' --processes 4 >/dev/null
head -n 1000   0,00s user 0,00s system 0% cpu 1,628 total
jf --import spacy --init 'nlp = spacy.load("en_core_web_sm")'   4   17,20s user 0,28s system 280% cpu 6,234 total
```

### Import json files

Import additional json files for mapping, merging and joining

```bash
 $ cat map.json 
{"bar": "world"}
 $ echo '{"hello": "bar"}'|jf --import foo=map.json '{hello: foo.get(.bar)}'
{
  "hello": "world"
}
```

This can be useful if you want to merge content from two json files. For example below we convert a users.jsonl into a users mapping by grouping all records based on the id-value of the record line and taking the first (and hopefully only) instance from the grouping. Next we take this mapping and use it to generate the user-data for each value in our orders.jsonl. Notice that since [json encodes dict keys always as strings](https://stackoverflow.com/questions/1450957/pythons-json-module-converts-int-dictionary-keys-to-strings), here we also need to convert our orders uid into a string.

```bash
 $ jf 'group_by(.id), {k: v[0] for k,v in x.items()}' users.jsonl > users.json
 $ jf --import users=users.json '{user: users.get(str(.uid)), ...}' orders.jsonl
{
  "uid": 123,
  "amount": 3,
  "item": "juice",
  "user": {
    "name": "bob",
    "id": 123,
    "address": "bobistreet"
  }
}
{
  "uid": 123,
  "amount": 2,
  "item": "milk",
  "user": {
    "name": "bob",
    "id": 123,
    "address": "bobistreet"
  }
}
{
  "uid": 124,
  "amount": 3,
  "item": "burgers",
  "user": {
    "name": "alice",
    "id": 124,
    "address": "alicestreet"
  }
}
```

## Various Input/output formats

```bash
 $ jf --output help
- clipboard
- csv
- excel
- feather
- html
- json
- jsonl
- latex
- markdown
- numpy
- parquet
- pickle
- py
- python
- string
- xarray
- xml
- yaml
```



```yaml
 $ jf --import users=users.json '{user: users.get(str(.uid)), ...}' orders.json --output yaml
- amount: 3
  item: juice
  uid: 123
  user:
    address: bobistreet
    id: 123
    name: bob
- amount: 2
  item: milk
  uid: 123
  user:
    address: bobistreet
    id: 123
    name: bob
- amount: 3
  item: burgers
  uid: 124
  user:
    address: alicestreet
    id: 124
    name: alice
```

```python
 $ jf --import users=users.json '{user: users.get(str(.uid)), ...}' orders.json --output py 
{'uid': 123, 'amount': 3, 'item': 'juice', 'user': {'name': 'bob', 'id': 123, 'address': 'bobistreet'}}
{'uid': 123, 'amount': 2, 'item': 'milk', 'user': {'name': 'bob', 'id': 123, 'address': 'bobistreet'}}
{'uid': 124, 'amount': 3, 'item': 'burgers', 'user': {'name': 'alice', 'id': 124, 'address': 'alicestreet'}}
```



```csv
 $ jf --import users=users.json '{user: users.get(str(.uid)), ...}' orders.json --output csv 
,uid,amount,item,user
0,123,3,juice,"{'name': 'bob', 'id': 123, 'address': 'bobistreet'}"
1,123,2,milk,"{'name': 'bob', 'id': 123, 'address': 'bobistreet'}"
2,124,3,burgers,"{'name': 'alice', 'id': 124, 'address': 'alicestreet'}"
```

### Flatten dictionary

```csv
 $ jf --import users=users.json '{user: users.get(str(.uid)), ...}, flatten()' orders.json --output csv
,uid,amount,item,user.name,user.id,user.address
0,123,3,juice,bob,123,bobistreet
1,123,2,milk,bob,123,bobistreet
2,124,3,burgers,alice,124,alicestreet
```

### More formats

By installing additional libraries, we can get some more output formats

```bash
 $ pip install lxml tabulate openpyxl pyarrow
```

```
 $ jf --import users=users.json '{user: users.get(str(.uid)), ...}' orders.json --output xml     
<?xml version='1.0' encoding='utf-8'?>
<data>
  <row>
    <index>0</index>
    <uid>123</uid>
    <amount>3</amount>
    <item>juice</item>
    <user>{'name': 'bob', 'id': 123, 'address': 'bobistreet'}</user>
  </row>
  <row>
    <index>1</index>
    <uid>123</uid>
    <amount>2</amount>
    <item>milk</item>
    <user>{'name': 'bob', 'id': 123, 'address': 'bobistreet'}</user>
  </row>
  <row>
    <index>2</index>
    <uid>124</uid>
    <amount>3</amount>
    <item>burgers</item>
    <user>{'name': 'alice', 'id': 124, 'address': 'alicestreet'}</user>
  </row>
</data>
```

```
 $ jf --import users=users.json '{user: users.get(str(.uid)), ...}, flatten()' orders.json --output markdown
|    |   uid |   amount | item    | user.name   |   user.id | user.address   |
|---:|------:|---------:|:--------|:------------|----------:|:---------------|
|  0 |   123 |        3 | juice   | bob         |       123 | bobistreet     |
|  1 |   123 |        2 | milk    | bob         |       123 | bobistreet     |
|  2 |   124 |        3 | burgers | alice       |       124 | alicestreet    |
```

### Binary output

Some formats are binary. You probably want to pipe them to a file and open it from there.

```bash
 $ jf --import users=users.json '{user: users.get(str(.uid)), ...}, flatten()' orders.json --output parquet 
PAR1 $L<{|{{	 &�5uid��&{{, $L &�5amount��&,8<Lljuicemilkburgers,6(milkburgers
$$&�
    5item��&�&�6(milkburgers, $L<bobalice,6(bobalice	 &�

5	user.name��&�	&6(bobalice, $L<{|{{	 &�
```

```bash
 $ jf --import users=users.json '{user: users.get(str(.uid)), ...}, flatten()' orders.json --output excel
P=�KSAMb��docProps/app.xmlM�=
                             1D��q��A�Bb@�R��{dC�B~�9��noF�
�+docProps/core.xml͒QK�0ǿ�佽�E���e�'���[Hn[Xӄ�ݷ7�[���1w���wp�B��/��d1݌���a�DA$}@�R�}n�|t��3�!(}T{�����!)�H�,�Bd�5Z舊|<�^��3v3�h�������P͜�;px~z��-l�H���d���e�[��l�����*8��F�{q��1���
```

```bash
 $ jf --import users=users.json '{user: users.get(str(.uid)), ...}, flatten()' orders.json --output excel >result.xlsx
 $ soffice result.xlsx
```

```
 $ jf x result.xlsx
{
  "Unnamed: 0": 0,
  "uid": 123,
  "amount": 3,
  "item": "juice",
  "user.name": "bob",
  "user.id": 123,
  "user.address": "bobistreet"
}
{
  "Unnamed: 0": 1,
  "uid": 123,
  "amount": 2,
  "item": "milk",
  "user.name": "bob",
  "user.id": 123,
  "user.address": "bobistreet"
}
{
  "Unnamed: 0": 2,
  "uid": 124,
  "amount": 3,
  "item": "burgers",
  "user.name": "alice",
  "user.id": 124,
  "user.address": "alicestreet"
}
```

## Extending

JF can be extended by importing your external python modules.

### Import your own custom functions

As any python modules you can also import your own modules found in a path pointed by the argument `--import_from`:

```bash
 $ cat examples/counter.py
from jf.meta import JFTransformation


class count(JFTransformation):
    def _fn(self, arr):
        for it in arr:
            yield len(it)

 $ cat dataset.jsonl|jf 'counter.count()' -c --import counter --import_from examples 
33
33
34
33
...
```

#### Example: Add audio duration data to common voice dataset

If we use the library binding from [Calling soxlib from python](http://anomalia.io/blog/Audio_length/index.html#Call-the-libsox-library-from-python) to get access to some sox functions, we can do some powerful transformations with jf. Saving the sox binding as `pysox.py`, below we use the [common voice dataset](https://commonvoice.mozilla.org/en/datasets) to create a `.json` description of the contents with some added metadata.

```bash
 $ CORPUSPATH="/path/to/commonvoice-corpus"
 $ jf '{audiometa: pysox.get_audioinfo(corpuspath + "/clips/" + .path), ...},
                  {audio: f"clips/{.path}", duration: .audiometa.signal.length/max(.audiometa.signal.channels, 1)/max(.audiometa.signal.rate, 1), ...}'
              $CORPUSPATH/dev.tsv
              --input "csv,sep=\t"
              --init "corpuspath='${CORPUSPATH}'"
              --import pysox --import_from examples
{
  "client_id": "25f51c66034cc323556a5af796cb084f898d9321959246e29a38c922c5f13087cb9a94f772c9da124844761c0009797e19662ddc5011a96dd532e98f6a0eb03b",
  "path": "common_voice_es_20245795.mp3",
  "sentence": "Se encuentra en Oceanía: Futuna.",
  "up_votes": 2,
  "down_votes": 0,
  "age": NaN,
  "gender": NaN,
  "accent": NaN,
  "locale": "es",
  "segment": NaN,
  "audiometa": {
    "encoding": {
      "bits_per_sample": 0,
      "encoding": 22,
      "opposite_endian": false,
      "reverse_bits": 0,
      "reverse_bytes": 0,
      "reverse_nibbles": 2146435072
    },
    "filename": "/media/.../cv-corpus-7.0-2021-07-21/es/clips/common_voice_es_20245795.mp3",
    "signal": {
      "channels": 1,
      "length": 191232,
      "mult": null,
      "precision": 0,
      "rate": 48000.0
    }
  },
  "audio": "clips/common_voice_es_20245795.mp3",
  "duration": 3.984
}
...
```

Here we use the forced input formatting to specify the [specific format to *pandas*](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.read_csv.html).

We could then further filter this dataset to select only audios with a length between `1...15s`, which is useful in some ASR model training scenarios.

```bash
 $ CORPUSPATH="/path/to/commonvoice-corpus"
 $ jf '{audiometa: pysox.get_audioinfo(corpuspath + "/clips/" + .path), ...},
                  {audio: f"clips/{.path}", duration: .audiometa.signal.length/max(.audiometa.signal.channels, 1)/max(.audiometa.signal.rate, 1), ...},
                  (.duration > 1 and .duration < 15)'
              $CORPUSPATH/dev.tsv
              --input csv,sep=\\t
              --init "corpuspath='${CORPUSPATH}'"
              --import pysox --import_from examples
{
  "client_id": "25f51c66034cc323556a5af796cb084f898d9321959246e29a38c922c5f13087cb9a94f772c9da124844761c0009797e19662ddc5011a96dd532e98f6a0eb03b",
  "path": "common_voice_es_20245795.mp3",
  "sentence": "Se encuentra en Oceanía: Futuna.",
  "up_votes": 2,
  "down_votes": 0,
  "age": NaN,
  "gender": NaN,
  "accent": NaN,
  "locale": "es",
  "segment": NaN,
  "audiometa": {
    "encoding": {
      "bits_per_sample": 0,
      "encoding": 22,
      "opposite_endian": false,
      "reverse_bits": 0,
      "reverse_bytes": 0,
      "reverse_nibbles": 2146435072
    },
    "filename": "/media/.../cv-corpus-7.0-2021-07-21/es/clips/common_voice_es_20245795.mp3",
    "signal": {
      "channels": 1,
      "length": 191232,
      "mult": null,
      "precision": 0,
      "rate": 48000.0
    }
  },
  "audio": "clips/common_voice_es_20245795.mp3",
  "duration": 3.984
}
{
  "client_id": "263ffb44bee3c3f3545b6654c32ce89044e71553c09805d60b20966d7186fcf34b6903226013870d0945ddd9cdd49a83ac1dd760280155e4beb3716b2cf57d9e",
  "path": "common_voice_es_18940511.mp3",
  "sentence": "Este café es muy popular.",
  "up_votes": 2,
  "down_votes": 0,
  "age": NaN,
  "gender": NaN,
  "accent": NaN,
  "locale": "es",
  "segment": NaN,
  "audiometa": {
    "encoding": {
      "bits_per_sample": 0,
      "encoding": 22,
      "opposite_endian": false,
      "reverse_bits": 0,
      "reverse_bytes": 0,
      "reverse_nibbles": 2146435072
    },
    "filename": "/media/.../cv-corpus-7.0-2021-07-21/es/clips/common_voice_es_18940511.mp3",
    "signal": {
      "channels": 1,
      "length": 168192,
      "mult": null,
      "precision": 0,
      "rate": 48000.0
    }
  },
  "audio": "clips/common_voice_es_18940511.mp3",
  "duration": 3.504
}
...
```

This could further be made more clean by defining a `get_duration(audiometa.signal)` function in the `pysox.py` so that we could simply write:

```bash
 $ jf '{audiometa: pysox.get_audioinfo(env.CORPUSPATH + "/clips/" + .path), ...}, {audio: f"clips/{.path}", duration: pysox.get_duration(.audiometa.signal), ...}' $CORPUSPATH/dev.tsv --input "csv,sep=\t" --import pysox --import_from examples
{
  "client_id": "25f51c66034cc323556a5af796cb084f898d9321959246e29a38c922c5f13087cb9a94f772c9da124844761c0009797e19662ddc5011a96dd532e98f6a0eb03b",
  "path": "common_voice_es_20245795.mp3",
  "sentence": "Se encuentra en Oceanía: Futuna.",
  "up_votes": 2,
  ...
```

Finally we can turn this into a script, `commonvoice.jf`:

```python
#!/usr/bin/env jf
#import pysox
#input csv,sep=\t

{audiometa: pysox.get_audioinfo(env.CORPUSPATH + "/clips/" + .path), ...}
{audio: f"clips/{.path}", duration: pysox.get_duration(.audiometa.signal), ...}
```

Which can be used like:

```bash
 $ ./commonvoice.jf $CORPUSPATH/dev.tsv --processes 3 --import_from examples|head
{
  "client_id": "25d033068bfdb4005002546358a715024c68802212b56da920347001d35d956ea6f66dfb8095f42f2cbdf19a1573f9ac5de2684de9746fd3e73e90f08ebd31f8",
  "path": "common_voice_es_19982238.mp3",
  "sentence": "Estaba rodeada de jardines y de un prado arbolado.",
  "up_votes": 2,
  "down_votes": 0,
  "age": "thirties",
  "gender": "female",
  "accent": NaN,
  "locale": "es",
  "segment": NaN,
  "audiometa": {
    "encoding": {
      "bits_per_sample": 0,
      "encoding": 22,
      "opposite_endian": false,
      "reverse_bits": 0,
      "reverse_bytes": 0,
      "reverse_nibbles": 2146435072
    },
    "filename": "/path/to/commonvoice/clips/common_voice_es_19982238.mp3",
    "signal": {
      "channels": 1,
      "length": 213120,
      "mult": null,
      "precision": 0,
      "rate": 48000.0
    }
  },
  "audio": "clips/common_voice_es_19982238.mp3",
  "duration": 4.44
}
{
  "client_id": "25d033068bfdb4005002546358a715024c68802212b56da920347001d35d956ea6f66dfb8095f42f2cbdf19a1573f9ac5de2684de9746fd3e73e90f08ebd31f8",
  "path": "common_voice_es_19982239.mp3",
  "sentence": "Al contrario la recepción del cine de Edison era individual.",
  "up_votes": 2,
  "down_votes": 0,
  "age": "thirties",
  "gender": "female",
  ...
```



### Import custom protocol handlers

Create a function named `jf_fetch_{proto}` to handle fetching from custom protocols:

```python
# examples/iotools.py
def jf_fetch_gs(fn):
    return b'{"hello": "world"}'

def jf_fetch_s3(fn):
    ...
```

JF will try to find a correctly named function to unknown protocols:

```bash
 $ jf "x" gs://my-training-data-1234567/datasets/cv-train.json --import iotools --import_from examples
Fetching gs://my-training-data-1234567/datasets/cv-train.json
{
  "hello": "world"
}
```

### Import custom data encoder/decode

```python
# serialization_tools.py
import msgpack

def jf_serialize_msg(data):
    return msgpack.packb(data, use_bin_type=True)

def jf_unserialize_msg(f):
    yield from msgpack.unpackb(f.read(), raw=False)
```

You now have access to input and output of `.msg` format

```bash
 $ jf "x" dataset.json --import serialization_tools --output msg > result.msg
 $ wc -c dataset.json
123777394 dataset.json
 $ wc -c result.msg
99015001 result.msg
 $ jf "x" --import iotools result.msg
{
  "hello": "world"
  ...
```

