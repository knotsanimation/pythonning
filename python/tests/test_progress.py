import logging
import time

from pythonning.progress import ProgressBar

LOGGER = logging.getLogger(__name__)


def test_progress_bar():
    # this is a simple execution test to check no exception is raised

    p = ProgressBar(
        prefix="\x1b[32mdownloading {bar_max} elements",
        suffix="[{bar_index:<2n}/{bar_max}] elapsed {elapsed_time:.2f}s\x1b[0m",
        width=32,
        max_value=25,
    )
    p.start()
    for x in range(25 + 1):
        time.sleep(0.01)
        p.add_progress(1)

    p.end()
    print("progress bar test finished !")

    p = ProgressBar(
        width=16,
        max_value=10,
    )
    p.start()
    for x in range(10 + 1):
        time.sleep(0.01)
        p.update()

    p.end()
    print("progress bar test finished !")
