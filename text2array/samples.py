from typing import Mapping, Union
import abc

FieldName = str
FieldValue = Union[float, int, str]


class SampleABC(metaclass=abc.ABCMeta):
    @property
    @abc.abstractmethod
    def fields(self) -> Mapping[FieldName, FieldValue]:
        pass
