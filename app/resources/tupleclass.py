"""
Contains the TupleClass to easily call `tuple(obj)` on any object of it.
"""

from dataclasses import dataclass


@dataclass
class TupleClass:
    """
    Abtract class to make objects easily transformable into tuples of itself
    """

    def __init__(self, *args, **kwargs) -> None:
        super.__init__(*args, **kwargs)

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n < len(vars(self)) - 1:
            attr = list(vars(self).keys())[self._n]
            self._n += 1
            return self.__getattribute__(attr)
        raise StopIteration
