import logging
import os
import stat
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
