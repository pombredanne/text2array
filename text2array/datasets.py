from collections.abc import \
    Iterable as IterableABC, MutableSequence as MutableSequenceABC, Sequence as SequenceABC
from typing import Iterable, Iterator, Sequence
import abc
import random

from .samples import Sample


class DatasetABC(Iterable[Sample], metaclass=abc.ABCMeta):  # pragma: no cover
    @abc.abstractmethod
    def batch(self, batch_size: int) -> Iterator['Batch']:
        pass

    def batch_exactly(self, batch_size: int) -> Iterator['Batch']:
        """Group the samples in the dataset into batches of exact size.

        If the number of samples is not divisible by ``batch_size``, the last
        batch (whose length is less than ``batch_size``) is dropped.

        Args:
            batch_size: Number of samples in each batch.

        Returns:
            The iterator of batches.
        """
        return (b for b in self.batch(batch_size) if len(b) == batch_size)


class Dataset(DatasetABC, Sequence[Sample]):
    """A dataset that fits in memory (no streaming).

    Args:
        samples: Sequence of samples the dataset should contain. This sequence should
            support indexing by a positive/negative index of type :obj:`int` or a
            :obj:`slice` object.
    """

    def __init__(self, samples: Sequence[Sample]) -> None:
        if not isinstance(samples, SequenceABC):
            raise TypeError('"samples" is not a sequence')

        self._samples = samples

    def __getitem__(self, index):
        return self._samples[index]

    def __len__(self) -> int:
        return len(self._samples)

    def shuffle(self) -> 'Dataset':
        """Shuffle the dataset.

        This method shuffles in-place if ``samples`` is a mutable sequence.
        Otherwise, a copy is made and then shuffled. This copy is a mutable
        sequence, so subsequent shuffling will be done in-place.

        Returns:
            The dataset object itself (useful for chaining).
        """
        if isinstance(self._samples, MutableSequenceABC):
            self._shuffle_inplace()
        else:
            self._shuffle_copy()
        return self

    def batch(self, batch_size: int) -> Iterator['Batch']:
        """Group the samples in the dataset into batches.

        Args:
            batch_size: Maximum number of samples in each batch.

        Returns:
            The iterator of batches.
        """
        if batch_size <= 0:
            raise ValueError('batch size must be greater than 0')

        for begin in range(0, len(self._samples), batch_size):
            end = begin + batch_size
            yield Batch(self._samples[begin:end])

    def _shuffle_inplace(self) -> None:
        assert isinstance(self._samples, MutableSequenceABC)
        n = len(self._samples)
        for i in range(n):
            j = random.randrange(n)
            temp = self._samples[i]
            self._samples[i] = self._samples[j]
            self._samples[j] = temp

    def _shuffle_copy(self) -> None:
        shuf_indices = list(range(len(self._samples)))
        random.shuffle(shuf_indices)
        shuf_samples = [self._samples[i] for i in shuf_indices]
        self._samples = shuf_samples


class StreamDataset(DatasetABC):
    """A dataset that streams its samples.

    Args:
        stream: Stream of examples the dataset should stream from.
    """

    def __init__(self, stream: Iterable[Sample]) -> None:
        if not isinstance(stream, IterableABC):
            raise TypeError('"stream" is not iterable')

        self._stream = stream

    def __iter__(self) -> Iterator[int]:
        return iter(self._stream)

    def batch(self, batch_size: int) -> Iterator['Batch']:
        """Group the samples in the dataset into batches.

        Args:
            batch_size: Maximum number of samples in each batch.

        Returns:
            The iterator of batches.
        """
        if batch_size <= 0:
            raise ValueError('batch size must be greater than 0')

        it, exhausted = iter(self._stream), False
        while not exhausted:
            batch: list = []
            while not exhausted and len(batch) < batch_size:
                try:
                    batch.append(next(it))
                except StopIteration:
                    exhausted = True
            if batch:
                yield Batch(batch)


# Need to import here to avoid circular dependency
from .batches import Batch
