from abc import ABC, abstractmethod


class JFTransformation(ABC):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    @abstractmethod
    def _fn(self, arr):
        """This method must be overwrite by actual transformation methods"""

    def __call__(self, arr):
        return self._fn(arr)
