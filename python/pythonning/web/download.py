import logging
import os
import shutil
import urllib.request
from pathlib import Path
from typing import Callable
from typing import Optional

from pythonning.caching import FilesCache


LOGGER = logging.getLogger(__name__)

_DOWNLOAD_CACHE = FilesCache("pythonning-downloadcache")
_DISABLE_CACHE_ENV_VAR = "PYTHONNING_DISABLE_DOWNLOAD_CACHE"


def clear_download_cache():
    """
    Delete any file that might have been cached since multiple sessions.
    """
    _DOWNLOAD_CACHE.clear()


def download_file(
    url: str,
    target_file: Path,
    use_cache: bool = False,
    step_callback: Optional[Callable[[int, int, int], object]] = None,
    user_agent: str = "Mozilla/5.0",
):
    """
    Download a single file from the web at the given url and display download progress in terminal.

    You can cache the result when you know that you may call this function
    multiple time for the same url.

    Args:
        url: url to download from, ensure it's a file.
        target_file: filesytem path of the file to download
        use_cache: True to use the cached downloaded file. Will create it the first time.
        step_callback:
            function called everytime the download progress one step.
            Arguments for the function are (block_number, block_size, total_size)
        user_agent: change the User-Agent header to fake the browser used for the connection
    """
    if os.getenv(_DISABLE_CACHE_ENV_VAR):
        use_cache = False

    if use_cache:
        cache_file = _DOWNLOAD_CACHE.get_file_cache(unique_id=url)
        if cache_file:
            LOGGER.debug(f"cache found, copying {cache_file} to {target_file} ...")
            shutil.copy2(cache_file, target_file)
            return

    url_opener = urllib.request.build_opener()
    # this prevents some website from blocking the connection (example: Blender)
    url_opener.addheaders = [("User-agent", user_agent)]

    with url_opener.open(url) as url_stream, open(target_file, "wb") as file:
        # the following code is mostly copied from :
        # - urllib.request.urlretrieve: not used because we need to edit addheaders above
        # - shutil.copyfileobj: not used because we need the step_callback

        headers = url_stream.info()
        blocksize = 1024 * 8  # shutil use: shutil.COPY_BUFSIZE
        blocknum = 0

        size = -1
        if "content-length" in headers:
            size = int(headers["Content-Length"])

        if step_callback:
            step_callback(blocknum, blocksize, size)

        while True:
            buf = url_stream.read(blocksize)
            if not buf:
                break

            file.write(buf)
            blocknum += 1
            if step_callback:
                step_callback(blocknum, blocksize, size)

    if use_cache:
        LOGGER.debug(f"creating cache from url {url} downloaded as {target_file} ...")
        cache_file = _DOWNLOAD_CACHE.cache_file(target_file, unique_id=url)
        LOGGER.debug(f"cache file created at {cache_file}")
