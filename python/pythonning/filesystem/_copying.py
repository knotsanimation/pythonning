import hashlib
import logging
import math
import os
import shutil
from pathlib import Path
from typing import Callable
from typing import Optional

from ._retrieving import get_dir_content
from pythonning.caching import FilesCache

LOGGER = logging.getLogger(__name__)

_COPYING_CACHE = FilesCache("pythonning-filesystem-copying")

_IS_WINDOWS = os.name == "nt"
COPY_BUFSIZE = 1024 * 1024 if _IS_WINDOWS else 64 * 1024


def copy_path_to(path: Path, target_path: Path):
    """
    Create a copy of the given filesystem object at the given path.

    Directory are recursively copied and files have their metadata preserved.

    For more complex behavior (symlink, ...) you can copy this function and modify it
    for your need.

    Args:
        path: Filesystem path to an existing file or directory
        target_path: Filesystem path to an existing file or directory, of the same type as the path argument.
    """
    if path.is_file():
        shutil.copy2(path, target_path)
    else:
        shutil.copytree(
            path,
            target_path,
        )


class _Progress:
    __slots__ = ("current",)

    def __init__(self):
        self.current: int = 0

    def next(self):
        self.current += 1


def _copyfileobj_readinto(
    fsrc,
    fdst,
    callback: Callable[[int, int], None],
    length: int = COPY_BUFSIZE,
):
    """
    COPY of :func:`shutil._copyfileobj_readinto` with added callback.

    readinto()/memoryview() based variant of copyfileobj().
    ``fsrc`` must support readinto() method and both files must be open in binary mode.

    Args:
        fsrc: IO object with readinto attribute
        fdst: IO object with write attribute
        callback:
            function called on each chunk of the file read. Size of the chunk correspond
            to the length parameter. Signature is: ("current chunk size", "chunk length")
        length: divide the file reading in chunks of the given length, in bytes.
    """
    # Localize variable access to minimize overhead.
    fsrc_readinto = fsrc.readinto
    fdst_write = fdst.write

    progress = 0
    with memoryview(bytearray(length)) as mv:
        while True:
            n = fsrc_readinto(mv)
            if not n:
                break
            elif n < length:
                with mv[:n] as smv:
                    fdst.write(smv)
            else:
                fdst_write(mv)

            progress += n
            callback(progress, length)


def _copyfileobj(
    fsrc,
    fdst,
    callback: Callable[[int, int], None],
    length: int = COPY_BUFSIZE,
):
    """
    COPY of :func:`shutil.copyfileobj` with added callback.

    copy data from file-like object fsrc to file-like object fdst

    Args:
        fsrc: IO object with readinto attribute
        fdst: IO object with write attribute
        callback:
            function called on each chunk of the file read. Size of the chunk correspond
            to the length parameter. Signature is: ("current chunk size", "chunk length")
        length: divide the file reading in chunks of the given length, in bytes.
    """

    # Localize variable access to minimize overhead.
    fsrc_read = fsrc.read
    fdst_write = fdst.write

    progress = 0
    while True:
        buf = fsrc_read(length)
        if not buf:
            break
        fdst_write(buf)
        progress += len(buf)
        callback(progress, length)


def _copyfile(
    src_file: Path,
    target_file: Path,
    callback: Optional[Callable[[int, int, int], None]] = None,
    chunk_size: int = COPY_BUFSIZE,
) -> Path:
    """
    A modified copy of :func:`shutil.copyfile`

    Args:
        src_file: filesytem path to an existing file
        target_file: filesytem path to a non-existing file
    """

    is_windows = os.name == "nt"

    file_size = os.stat(src_file).st_size

    def _callback_wrapper(chunk: int, chunk_size: int):
        if callback:
            callback(chunk, chunk_size, file_size)

    with open(src_file, "rb") as fsrc:
        with open(target_file, "wb") as fdst:
            # Windows, see:
            # https://github.com/python/cpython/pull/7160#discussion_r195405230
            if is_windows and file_size > 0:
                _copyfileobj_readinto(
                    fsrc,
                    fdst,
                    callback=_callback_wrapper,
                    length=min(file_size, chunk_size),
                )
                return target_file

            # XXX: removed fast copy for other platforms for simplicity

            _copyfileobj(fsrc, fdst, callback=_callback_wrapper, length=chunk_size)

    return target_file


def _hash_file(src_file: Path) -> str:
    """
    Create a hash of the given file path that is stable between python sessions.

    This is a minimal implementation that prefer smaller hash size over accuracy.

    Args:
        src_file: filesystem path to an existing file.

    Returns:
        hash as string
    """
    stats = os.stat(src_file)
    identifier = str(src_file) + repr(stats)
    return hashlib.sha256(bytes(identifier, "utf-8")).hexdigest()


def copyfile(
    src_file: Path,
    target_path: Path,
    callback: Optional[Callable[[int, int, int], None]] = None,
    chunk_size: int = COPY_BUFSIZE,
    use_cache: bool = False,
) -> Path:
    """
    Copy src file to target and preserve file stats.

    Similar to :func:`shutil.copy2` but with:

    * a callback parameter: Callback is only useful for file above few MB as is it not
      called enough often for smaller files.
    * a cache option: for files on slow network that are often accessed. Note the
      lifetime of the cache is not guaranteed as being stored on the system default
      temporary location.

    If you know your source is a symlink and you would like to copy it to target as
    a symlink then use ``shutil.copy(follow_symlinks=False)`` instead.

    Args:
        src_file: filesystem path to an existing file
        target_path: filesystem path to a non-existing file or an existing directory.
        callback:
            function called on each chunk of the file read. Signature is :
            ("current chunk", "chunk size", "total size") -> None
            all values expressed in bytes.
        chunk_size:
            size in bytes of each chunk of the file to read. Must not be bigger
            than the file size itself.
            Lower value increase the number of calls to callback but slow the process.
        use_cache:
            True to store and retrieve the file from a local cache. Useful when the file
            is stored on slow network locations. The cache is preserved between sessions.
            Note if the cache doesn't exist the first time this would imply 2 copy operation,
            one to create the cache, and one to copy to target_path. Both would call
            the callback making the total 2 times the size of the src_file.

    Returns:
        target_path
    """
    new_callback = callback

    if use_cache:
        cache_hash = _hash_file(src_file)
        cache_file = _COPYING_CACHE.get_file_cache(unique_id=cache_hash)

        if cache_file:
            src_file = cache_file

        else:

            def _first_callback(_chunk: int, _chunk_size: int, _total: int):
                # _total is doubled because we will copy the file 2 times
                callback(_chunk, _chunk_size, _total * 2)

            def _copy_function(src_path: Path, dst_path: Path):
                copyfile(
                    src_path,
                    dst_path,
                    callback=_first_callback,
                    chunk_size=chunk_size,
                    use_cache=False,
                )

            src_file = _COPYING_CACHE.cache_file(
                src_file,
                unique_id=cache_hash,
                copy_function=_copy_function,
            )

            def _second_callback(_chunk: int, _chunk_size: int, _total: int):
                # _total is doubled because we will copy the file 2 times
                callback(_total + _chunk, _chunk_size, _total * 2)

            new_callback = _second_callback

    if target_path.is_dir():
        target_path = target_path / src_file.name

    if target_path.exists():
        raise FileExistsError(f"target {target_path} already exists")

    _copyfile(src_file, target_path, callback=new_callback, chunk_size=chunk_size)
    shutil.copystat(src_file, target_path)
    return target_path


def copytree(
    src_dir: Path,
    target_dir: Path,
    callback: Callable[[Path, int, int], None],
    **kwargs,
):
    """
    Recursively copy a directory tree and return the destination directory.

    Difference with ``shutil.copytree`` is the ability to use callback called on each
    path copied. Useful to display a progress bar for example.

    Args:
        src_dir: filesystem path to an existing directory
        target_dir: filesystem path to an existing directory
        callback:
            function called on each path copied with:
            ("path", "path index", "total number of paths")
        kwargs: passed to :func:`shutil.copytree`
    """
    items_count = len(get_dir_content(src_dir, recursive=True))

    progress = _Progress()

    def _copy_func(_src, _dst, *, _follow_symlinks=True):
        if kwargs.get("copy_function"):
            kwargs["copy_function"](_src, _dst, follow_symlinks=_follow_symlinks)
        else:
            shutil.copy2(_src, _dst, follow_symlinks=_follow_symlinks)
        # called for files
        callback(Path(_src), progress.current, items_count)
        progress.next()

    def _ignore_func(_src_dir, _content_names):
        # called for dirs
        if not str(src_dir) == str(_src_dir):
            callback(Path(_src_dir), progress.current, items_count)
        progress.next()
        kwargs_func = kwargs.get("ignore")
        return kwargs_func(_src_dir, _content_names) if kwargs_func else []

    shutil.copytree(
        src_dir,
        target_dir,
        copy_function=_copy_func,
        ignore=_ignore_func,
        **kwargs,
    )

    return target_dir


def move_directory_content(
    src_directory: Path,
    target_directory: Path,
    exists_ok: bool = False,
    recursive: bool = True,
):
    """
    Move (NOT a copy) all the files and directories in the source to the target.

    Handle move between different disk roots.

    Args:
        src_directory: filesystem path to an existing directory
        target_directory: filesystem path to an existing directory
        exists_ok: True to ignore if the target file already exists, else will raise en error.
        recursive:
            True to also process all subdirectory recursively to not miss any files.
    """
    for src_path in src_directory.glob("*"):
        target = target_directory / src_path.name
        if target.exists() and exists_ok:
            if src_path.is_dir() and recursive:
                move_directory_content(src_path, target, exists_ok=True, recursive=True)
            continue
        if target.exists():
            raise FileExistsError(f"File already exists on disk: <{target}>")
        # use shutil instead of os.rename to handle move between disks
        shutil.move(src_path, target)
        if src_path.is_dir() and recursive:
            move_directory_content(src_path, target, exists_ok=True, recursive=True)
