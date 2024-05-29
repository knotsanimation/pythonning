import contextlib
import time
from typing import Callable


@contextlib.contextmanager
def timeit(message: str, stream: Callable[[str], None], decimals: int = 2):
    """
    Measure the time took in seconds for a process to run and log it.

    Example::

        fib = lambda n: n if n < 2 else fib(n-1) + fib(n-2)
        with timeit("process took ", print):
            result = fib(27)

    Args:
        message: arbitary message that is appended the duration time and passed to ``stream``
        stream: a callable exeucted at the end and which receive the message formated with the duration.
        decimals: amoutn of number after the decimal to keep when rounding the duration
    """
    start = time.time()
    try:
        yield
    finally:
        end = time.time()
        duration = "{:.{}f}".format(end - start, decimals)
        stream(f"{message}{duration}s")
