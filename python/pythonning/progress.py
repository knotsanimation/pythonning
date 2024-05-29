import contextlib
import logging
import math
import sys
import time
from typing import Optional

from .mathing import remap_range

LOGGER = logging.getLogger(__name__)


class ProgressBar:
    """
    A simple progress bar displayed in the given stream.

    The recommended usage is to ``start()`` the progress, then call ``add_progress()``
    during the measured process, and finished by calling ``end()``.

    You can also create an "infinite" progress bar by not calling ``add_progress`` or
    ``set_progress`` and just calling ``update()`` instead.

    Tips: you can add coloring by adding the color special character in the
    prefix and suffix strings.

    **Text Formatting**

    Prefix and suffix are formatted with the following tokens :

    * ``bar_min``: minimal value of the bar specified by user
    * ``bar_max``: maximal value of the bar specified by user
    * ``bar_index``: the current value of the bar
    * ``elapsed_time``: amount of time since first progress call, in seconds.

    String are formatted as usual with the ``str.format`` function.

    Example::

        suffix="[{bar_index:<2n}/{bar_max}] elapsed {elapsed_time:.2f}s"

    **Changing style**

    To change the bar style you can subclass it and override the class attributes.

    Example::

        class MyProgressBar(ProgressBar):
            bar_fill = "#"

    **Future improvement**

    * Missing time estimation features.

    Args:
        min_value: value that is considered the start of the progress bar
        max_value: value that is considered the end of the progress bar
        width: width of the progress bar in number of characters, excluding contextual info
        prefix:
            string to format and add before the progress bar. see formatting documentation.
        suffix:
            string to format and add after the progress bar. see formatting documentation.
        stream: IO object to write the progress bar to
        hide_cursor: hide blinking cursor in stdout while the progress bar is displaying
    """

    bar_before = " |"
    bar_after = "| "
    # use only one character long string else unexpected behavior could occur.
    bar_fill = "█"
    bar_empty = " "

    def __init__(
        self,
        min_value: float = 0.0,
        max_value: float = 1.0,
        width: int = 32,
        prefix: str = "",
        suffix: str = "",
        stream=sys.stdout,
        hide_cursor: bool = True,
    ):
        # those can be set at any time
        self.prefix: str = prefix
        self.suffix: str = suffix

        self._width: int = width
        self._user_index: float = min_value
        self._user_min: float = min_value
        self._user_max: float = max_value
        self._stream = stream
        self._is_ended: bool = False
        self._had_progress: bool = False
        self._start_time: Optional[float] = None
        self._hide_cursor: bool = hide_cursor
        self._is_cursor_visible: bool = True
        self._update_number: int = 0

    def __del__(self):
        # safety to ensure the cursor is set back to visible once the object is removed
        self.set_cursor_visibility(visible=True)

    @property
    def max_value(self) -> float:
        return self._user_max

    @max_value.setter
    def max_value(self, new_max_value: float):
        self._user_max = new_max_value
        if self._had_progress:
            self.update()

    @property
    def min_value(self) -> float:
        return self._user_min

    @min_value.setter
    def min_value(self, new_min_value: float):
        self._user_min = new_min_value
        if self._had_progress:
            self.update()

    @property
    def _bar_width(self) -> int:
        """
        Returns:
            current width in characters units of the bar
        """
        bar_index = remap_range(
            value=self._user_index,
            source_min=self._user_min,
            source_max=self._user_max,
            target_min=0.0,
            target_max=self._width,
        )
        return math.floor(bar_index)

    @property
    def _time_elapsed(self) -> float:
        """
        Returns:
         time elapsed since start, in seconds
        """
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    def set_progress(self, total_progress: float, new_maximum: Optional[float] = None):
        """
        Make the bar move up to the given value.

        Value is expressed in the same unit as given during instancing to the
        max value. As such the value given can't be bigger than the max.

        Args:
            total_progress: same unit as maximum value
            new_maximum: optionally change the maximum value of the progress bar
        """
        self._had_progress = True

        if new_maximum is not None:
            self._user_max = new_maximum

        self._user_index = min(total_progress, self._user_max)
        self.update()

    def add_progress(self, progress_amount: float, new_maximum: Optional[float] = None):
        """
        Make the bar progress by the given amount.

        Amount is expressed in the same unit as given during instancing to the
        max value. As such amount given can't be bigger than this value.

        Args:
            progress_amount: same unit as maximum value
            new_maximum: optionally change the maximum value of the progress bar
        """
        self._had_progress = True

        if new_maximum is not None:
            self._user_max = new_maximum

        self._user_index = min(self._user_index + progress_amount, self._user_max)
        self.update()

    def start(self):
        """
        Display the progress bar for the first time.

        Not mandatory to be called.
        """
        self.update()

    def end(self):
        """
        Stop the progress bar, so it doesn't update anymore.

        Recommended to always be called.
        """
        self._is_ended = True
        # just add a new line
        print(file=self._stream)
        self.set_cursor_visibility(visible=True)

    def set_cursor_visibility(self, visible: bool):
        """
        Add or remove a special character that make the stream cursor visible or not.
        """
        if visible and not self._is_cursor_visible:
            print("\x1b[?25n", end="", file=self._stream)
            self._is_cursor_visible = True
        elif not visible and self._is_cursor_visible:
            print("\x1b[?25l", end="", file=self._stream)
            self._is_cursor_visible = False

    def _format_text(self, text: str) -> str:
        return text.format(
            elapsed_time=self._time_elapsed,
            bar_min=self._user_min,
            bar_max=self._user_max,
            bar_index=self._user_index,
        )

    def update(self):
        """
        Visually update the progress bar.

        Called automatically but can be manually called to increase refresh rate.
        """
        if self._is_ended:
            return

        if self._start_time is None:
            self._start_time = time.time()

        if self._hide_cursor:
            self.set_cursor_visibility(visible=False)

        if self._had_progress:
            bar_fill_width: int = self._bar_width
            bar_empty_width: int = self._width - bar_fill_width
            bar_text: str = (
                self.bar_fill * bar_fill_width + self.bar_empty * bar_empty_width
            )
            bar_text = f"{self.bar_before}{bar_text}{self.bar_after}"
        else:
            expected_length = len(self.bar_before) + len(self.bar_after) + self._width
            bar_text = "." * (self._update_number % 3 + 1)
            bar_text = f" {bar_text}".ljust(expected_length)

        suffix_text = self._format_text(self.suffix)
        prefix_text = self._format_text(self.prefix)

        out_text = f"{prefix_text}{bar_text}{suffix_text} "
        print("\r" + out_text, end="", file=self._stream)
        self._stream.flush()

        self._update_number += 1


class DownloadProgressBar(ProgressBar):
    """
    A progress bar for downloads, expressed in MB units.

    Recommended usage with :any:`pythonning.web.download.download_file`.

    Note the ``prefix`` and ``suffix`` argument are already consumed.
    """

    byte_to_MB = 9.5367e-7

    def __init__(self, *args, **kwargs):
        super().__init__(
            prefix="downloading",
            suffix="[{bar_index:<2.1f}MB/{bar_max:.1f}MB] elapsed {elapsed_time:.2f}s",
            *args,
            **kwargs,
        )

    def show_progress(self, block_number, block_size, total_size):
        """
        To be used as callback during a download operation.

        Args:
            block_number: current block being downloaded, variable over time.
            block_size: size of each download block, static over time.
            total_size:
                total size of all the block to download, static over time.
                might not be provided which correspond to a value < 1.
        """
        if total_size < 1:
            self.update()
        else:
            downloaded = block_number * block_size
            self.set_progress(
                total_progress=downloaded * self.byte_to_MB,
                new_maximum=total_size * self.byte_to_MB,
            )


@contextlib.contextmanager
def catch_download_progress(**kwargs):
    """
    A context manager to display a Download progress bar and handle its cleaning.

    Make sure any stdout call (print, loggers) are done after the context manager has exit.

    Example::

        print("starting download")
        with catch_progress() as progressbar:
            download_file(step_callback=progressbar.show_progress)
        print("downloading finished")

    Args:
        kwargs:
            kwargs passed to DownloadProgressBar
            (``prefix`` and ``suffix`` are already consumed).
    """
    progress_bar = DownloadProgressBar(**kwargs)
    progress_bar.start()
    try:
        yield progress_bar
    finally:
        progress_bar.end()
