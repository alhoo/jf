from jf.meta import JFTransformation


class count(JFTransformation):
    def _fn(self, arr):
        for it in arr:
            yield len(it)
