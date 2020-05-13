import jf.sklearn_import
import pandas as pd


class ColumnSelector:
    def __init__(self, column):
        self.column = column

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        if isinstance(X, list):
            X = pd.DataFrame(X)
        # ret = [x[self.column] for x in X]
        return X[self.column]


def trainer(args, arr):
    params = args(arr)
    model = params

    data, y = list(zip(*list(map(lambda x: [x[0], x[1]], arr))))
    try:
        data = [x.dict() for x in data]
    except:
        pass
    print(f"Training the model ({model}):")
    model.fit(data, y)

    yield model


def persistent_trainer(args, arr):
    import pickle

    params = args(arr)
    ofn, model = params

    model = next(trainer(lambda x: model, arr))

    print(f"Saving model to {ofn}")
    with open(ofn, "wb") as f:
        f.write(pickle.dumps(model))
    yield model


class importResolver:
    def __getattribute__(self, k):
        if k == "persistent_trainer":
            return persistent_trainer
        if k == "trainer":
            return trainer
        if k == "ColumnSelector":
            return ColumnSelector
        else:
            mod = jf.sklearn_import.import_from_sklearn(k)
            if mod is not None:
                return mod
        print(f"Failed to import {k}")


import_resolver = importResolver()
