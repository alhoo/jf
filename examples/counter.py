from jf.meta import JFTransformation


class sum(JFTransformation):
    def _fn(self, arr):
        s = __builtins__["sum"]([it for it in arr])
        print(s)
        yield s


class count(JFTransformation):
    def _fn(self, arr):
        for it in arr:
            yield len(it)
