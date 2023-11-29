import logging
import os
import shutil
import stat
import zipfile
from pathlib import Path

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
