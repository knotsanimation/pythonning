import logging
import os
import shutil
import stat
import zipfile
from pathlib import Path
from typing import Callable

LOGGER = logging.getLogger(__name__)


def set_path_read_only(path: Path):
    """
    Remove write permissions for everyone on the given file.

    Does not touch other permissions.

    References:
        - [1] https://stackoverflow.com/a/38511116/13806195
    """
    NO_USER_WRITING = ~stat.S_IWUSR
    NO_GROUP_WRITING = ~stat.S_IWGRP
    NO_OTHER_WRITING = ~stat.S_IWOTH
    NO_WRITING = NO_USER_WRITING & NO_GROUP_WRITING & NO_OTHER_WRITING

    current_permissions = stat.S_IMODE(os.lstat(path).st_mode)
    os.chmod(path, current_permissions & NO_WRITING)


def get_dir_content(src_dir: Path, recursive=True) -> list[Path]:
    """
    Return a list of paths this directory contains.

    Return the whole files and directory tree if recursive=True.
    Be aware that recursive parsing can take some time for big file trees.

    Args:
        src_dir: filesystem path to an existing directory
        recursive: True to recursively process subdirectories

    Returns:
        list of absolute existing paths to file and directories
    """
    children = os.scandir(src_dir)
    if not recursive:
        return [Path(path) for path in children]

    recursive_children = []

    for child_entry in children:
        child_path = Path(child_entry.path)
        recursive_children.append(Path(child_entry.path))
        if child_entry.is_dir():
            recursive_children += get_dir_content(child_path, recursive=True)

    return recursive_children


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
    length: int = shutil.COPY_BUFSIZE,
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
    length: int = shutil.COPY_BUFSIZE,
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
    callback: Callable[[int, int, int], None],
    chunk_size: int = shutil.COPY_BUFSIZE,
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


def copyfile(
    src_file: Path,
    target_path: Path,
    callback: Callable[[int, int, int], None],
    chunk_size: int = shutil.COPY_BUFSIZE,
) -> Path:
    """
    Copy src file to target and preserve file stats.

    Similar to :func:`shutil.copy2` but with a callback parameter. Callback is only
    useful for file above few MB as is it not called enough often for smaller files.

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

    Returns:
        target_path
    """
    if target_path.is_dir():
        target_path = target_path / src_file.name

    if target_path.exists():
        raise FileExistsError(f"target {target_path} already exists")

    _copyfile(src_file, target_path, callback=callback, chunk_size=chunk_size)
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
        if not str(src_dir) == _src_dir:
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


def extract_zip(zip_path: Path, remove_zip=True):
    """
    Exract the given zip archive content in the directory it is in.

    Args:
        zip_path: path to an existing zip file on the filesystem.
        remove_zip: True to delete the zip once extracted

    Returns:
        root directory the extracted file can be found at
    """
    extract_root = zip_path.parent
    with zipfile.ZipFile(zip_path, "r") as zip_file:
        zip_file.extractall(extract_root)

    if remove_zip:
        zip_path.unlink()

    return extract_root


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
