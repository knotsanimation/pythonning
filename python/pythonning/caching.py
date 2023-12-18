import hashlib
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional

LOGGER = logging.getLogger(__name__)


def _hash_str(string: str) -> str:
    """
    Create a hash of the given string that is stable between python sessions.
    """
    return hashlib.sha256(bytes(string, "utf-8")).hexdigest()


class FilesCache:
    """
    Create a cache to store single files, that can be shared across python sessions.

    The lifetime of the cache is not guarantee as it is stored in the system temporary
    location which might be wiped-out independently.

    Args:
        unique_name:
            it is recommended to have a name unique across all the infrastructure, but not
            mandatory as the unique_id delivered by file is more important ot avoid collisions.
        location:
            filesystem path to an existing directory.
            By default in the system default temporary location, but you can provide you own.
    """

    def __init__(self, unique_name: str, location: Optional[Path] = None):
        self._name: str = unique_name
        self._root: Path = location or Path(tempfile.gettempdir())
        self._path: Path = self._root / self._name

    @property
    def exists(self) -> bool:
        return self._path.exists()

    @property
    def is_empty(self) -> bool:
        if not self.exists:
            return True
        return not next(os.scandir(self._path), None)

    def cache_file(self, file_path: Path, unique_id: str) -> Path:
        """

        Args:
            file_path: filesystem path to an existing file to cache
            unique_id:
                unique identifier to characterize the file to cache and allow to retrieve
                a cache given a similar unique_id

        Returns:
            filesystem path to the cached file
        """
        if not self.exists:
            LOGGER.debug(f"creating cache directory <{self._path}>")
            self._path.mkdir()

        cache_prefix = _hash_str(unique_id)

        temp_folder = Path(
            tempfile.mkdtemp(
                prefix=cache_prefix,
                dir=self._path,
            )
        )

        LOGGER.debug(f"creating copy in cache <{temp_folder}>")
        shutil.copy2(file_path, temp_folder)
        cache_file = temp_folder / file_path.name
        if not cache_file.exists():
            raise RuntimeError(f"Unkown issue: cache not created at <{cache_file}>")

        return cache_file

    def clear(self):
        """
        Delete all the file cached.
        """
        if not self.exists:
            return
        LOGGER.debug(f"removing cache <{self._path}> ...")
        shutil.rmtree(self._path)

    def get_file_cache(self, unique_id: str) -> Optional[Path]:
        """
        Get the potential cache file for the corresponding identifier.

        Args:
            unique_id:
                unique identifier characterizing the cached filed

        Returns:
            filesystem path to an existing file or None if no cache found.
        """
        if not self.exists:
            return None

        cache_prefix = _hash_str(unique_id)

        tempfolder: list[Path] = list(self._path.glob(f"{cache_prefix}*"))
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
            # the system might have cleared the tmp folder but leaved the directories
            return None

        # you must always have a single file inside, as defined in cache_file()
        return cache_file[0]
