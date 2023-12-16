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
