from itertools import islice
from jf import service
from jf.ml import import_resolver as ml
from jf.process import Map, Col, First
from examples.text_model import TextModel
import pickle
import os
import jf

MODEL_FILE = "model.pkl"

if not os.path.exists("model.pkl"):
    # Train a model
    dataset = jf.input.read_file("dataset.jsonl.gz")

    x = Col()

    # Transform the dataset into training data
    transformations = [
        First(1000),
        Map([x.detection_data.data.analysis.description, x.resolution]),
    ]

    # Transform the training data into a machine learned (persistent) model
    transformations.append(
        ml.persistent_trainer(MODEL_FILE, TextModel() ),
    )
else:
    # Load the previously trained model
    dataset = []

    transformations = [ml.model_loader(MODEL_FILE)]

# Finally transform the model into a service
transformations.append(
    service.RESTful(port=8000)
)

# Execute the JF pipeline
for it in jf.process.Pipeline(*transformations).transform(dataset, gen=True):
    print(it)
