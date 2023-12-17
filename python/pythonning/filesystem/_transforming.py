import logging
import zipfile
from pathlib import Path

LOGGER = logging.getLogger(__name__)


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
