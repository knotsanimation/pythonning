import hashlib
import logging
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable
from typing import Optional


LOGGER = logging.getLogger(__name__)

_DOWNLOAD_CACHE_ROOT = Path(tempfile.gettempdir()) / "pythonning-downloadcache"
_DISABLE_CACHE_ENV_VAR = "PYTHONNING_DISABLE_DOWNLOAD_CACHE"


def _hash_url(url: str) -> str:
    # we need a stable hash between python executions
    return hashlib.sha256(bytes(url, "utf-8")).hexdigest()


def _get_download_cache(source_url: str) -> Optional[Path]:
    """
    Find if the given url has already been cached.
    """
    if not _DOWNLOAD_CACHE_ROOT.exists():
        return None

    prefix = _hash_url(source_url)

    tempfolder: list[Path] = list(_DOWNLOAD_CACHE_ROOT.glob(f"{prefix}*"))
    if len(tempfolder) > 1:
        # should not happen but safety check
        LOGGER.warning(
            f"found multiple download cache for the same url in {tempfolder}"
        )

    tempfolder: Optional[Path] = tempfolder[0] if tempfolder else None
    if not tempfolder:
        return None

    cache_file = list(tempfolder.glob("*"))
    if not cache_file:
        return None

    # you must always have a single file inside, as defined in _create_cache
    return cache_file[0]


def _create_cache(file: Path, source_url: str) -> Path:
    """
    Create a cache for the provided file that has been downloaded from the given url.

    Path to the cached file is returned.
    """
    if not _DOWNLOAD_CACHE_ROOT.exists():
        LOGGER.debug(f"creating download cache root directory {_DOWNLOAD_CACHE_ROOT}")
        _DOWNLOAD_CACHE_ROOT.mkdir()

    # TODO should this be cleaned as this package should be rez agnostic ?
    build_name = os.getenv("REZ_BUILD_PROJECT_NAME", "none")
    build_version = os.getenv("REZ_BUILD_PROJECT_VERSION", "none")
    prefix = _hash_url(source_url)
    suffix = f"{build_name}-{build_version}"

    temp_folder = Path(
        tempfile.mkdtemp(
            prefix=prefix,
            suffix=suffix,
            dir=_DOWNLOAD_CACHE_ROOT,
        )
    )
    LOGGER.debug(f"creating copy in cache <{temp_folder}>")
    shutil.copy2(file, temp_folder)
    cache_file = temp_folder / file.name
    assert cache_file.exists(), cache_file
    return cache_file


def clear_download_cache():
    """
    Delete any file that might have been cached since multiple sessions.
    """
    if not _DOWNLOAD_CACHE_ROOT.exists():
        return
    LOGGER.debug(f"removing download cache <{_DOWNLOAD_CACHE_ROOT}> ...")
    shutil.rmtree(_DOWNLOAD_CACHE_ROOT)


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
        cache_file = _get_download_cache(url)
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
        cache_file = _create_cache(target_file, url)
        LOGGER.debug(f"cache file created at {cache_file}")
