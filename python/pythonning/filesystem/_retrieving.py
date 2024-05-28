import logging
import os
from pathlib import Path
from typing import List

LOGGER = logging.getLogger(__name__)


def get_dir_content(src_dir: Path, recursive=True) -> List[Path]:
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
