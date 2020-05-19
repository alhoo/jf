from jf.process import Map, Col
from jf.ml import import_resolver as ml

x = Col()

def TextModel():
    return ml.make_pipeline(
        Map(x if x is not None else ''),  # Swap nones to empty strings
        ml.make_union(
            ml.CountVectorizer(),
            ml.CountVectorizer(analyzer="char", ngram_range=(4,4))),
        ml.LogisticRegression()
    )
