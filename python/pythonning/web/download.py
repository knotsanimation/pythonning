import cgi
import logging
import os
import shutil
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Callable
from typing import Optional

from pythonning.caching import FilesCache


LOGGER = logging.getLogger(__name__)

_DOWNLOAD_CACHE = FilesCache("pythonning-downloadcache")
_DISABLE_CACHE_ENV_VAR = "PYTHONNING_DISABLE_DOWNLOAD_CACHE"


def get_url_filename(url, **kwargs) -> str:
    """
    Retrieve the filename from the given url header response.

    Not all urls might define a filename in their header and the function will raise
    in that case.

    References:
        - [1] https://stackoverflow.com/a/49733575/13806195

    Args:
        url: a valid web url whose request should return a header
        kwargs: passed to :func:`urllib.request.urlopen`
    """
    remotefile = urllib.request.urlopen(url, **kwargs)
    contentdisposition = remotefile.info()["Content-Disposition"]
    if not contentdisposition:
        raise ValueError(f"Missing 'Content-Disposition' header in '{url}' response.")
    _, params = cgi.parse_header(contentdisposition)
    filename = params["filename"]
    return filename


def get_url_content_type(url, **kwargs) -> str:
    """
    Retrieve the Content-Type the given url header response.

    Examples::

        image/jpeg
        image/svg+xml
        text/html; charset=utf-8
        application/octet-stream

    References:
        - [1] https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Type
        - [2] http://www.iana.org/assignments/media-types/media-types.xhtml

    Args:
        url: a valid web url whose request should return a header
        kwargs: passed to :func:`urllib.request.urlopen`
    """
    remotefile = urllib.request.urlopen(url, **kwargs)
    return remotefile.info()["Content-Type"]


def guess_url_filename(url: str, **kwargs) -> str:
    """
    Try to find the most plausible filename from the given filename.

    We try in the order:

    1. find it from the header's Content-Disposition filename attribute.
    2. extract a filename from the url string last component

       * if the filename doesn't have a file extension, try to guess it from the
         header's Content-Type attribute

    If you know both of this method would fail, you can at least try to get the
    file extension with :func:`get_url_content_type`

    The returned output robustness widly depends on the url you gave.

    Args:
        url: a valid web url
        kwargs: passed to :func:`urllib.request.urlopen`

    Returns:
        a file name that may not have a file extension
    """
    # 1.
    try:
        return get_url_filename(url, **kwargs)
    except ValueError:
        pass

    # 2.
    url_parsed = urllib.parse.urlparse(url)
    url_basename = urllib.parse.unquote(url_parsed.path)
    file = Path(url_basename)
    if not file.suffix:
        content_type = get_url_content_type(url, **kwargs)
        content_type = content_type.split(";")[0]
        type_, subtype = content_type.split("/")
        if type_ in ["image", "video", "audio", "text"]:
            # we remove the "+" for some case like svg+xml
            suffix = "." + subtype.split("+")[0]
            return file.with_suffix(suffix).name

    return file.name


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

    **Tip to download Google Drive files:**

    Extract the ID from whatever url you got and replace it in the following:
    ``https://drive.usercontent.google.com/download?id=YOURID&export=download&authuser=0&confirm=t``

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
        # TODO expose blocksize ?
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


def download_file_smart(
    url: str,
    target_dir: Path,
    use_cache: bool = False,
    step_callback: Optional[Callable[[int, int, int], object]] = None,
    user_agent: str = "Mozilla/5.0",
) -> Path:
    """
    Same as :func:`download_file` but the function guess the target filename from the url.

    Args:
        url: url to download from, ensure it's a file.
        target_dir: filesytem path to an existing directory to downlaod the file to.
        use_cache: True to use the cached downloaded file. Will create it the first time.
        step_callback:
            function called everytime the download progress one step.
            Arguments for the function are (block_number, block_size, total_size)
        user_agent: change the User-Agent header to fake the browser used for the connection

    Returns:
        filesystem path of the downloaded file
    """
    target_file = target_dir / get_url_filename(url)
    download_file(
        url=url,
        target_file=target_file,
        use_cache=use_cache,
        step_callback=step_callback,
        user_agent=user_agent,
    )
    return target_file
