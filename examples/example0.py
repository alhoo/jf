from pprint import pprint
import jf
from jf.process import Map, Col, Pipeline

# Define the x that represents one sample in your dataset
x = Col()

dataset = jf.input.read_file("dataset.jsonl.gz")

# Use the x as you would use it in your command lines
transformations = [Map(dict(id=x.id, energy=x.energy))]

transformed_dataset = jf.process.Pipeline(*transformations).transform(dataset)
pprint(transformed_dataset)
