import logging
import os
import shutil
import sys
from pathlib import Path

# XXX: we cannot use rezbuild_utils as it have a require on pythonning

LOGGER = logging.getLogger(__name__)


def build():
    if not os.getenv("REZ_BUILD_INSTALL") == "1":
        LOGGER.info(f"skipped")
        return

    source_dir = Path(os.environ["REZ_BUILD_SOURCE_PATH"])
    target_dir = Path(os.environ["REZ_BUILD_INSTALL_PATH"])

    file_to_copy = source_dir / "python"

    LOGGER.debug(f"copying {file_to_copy} to {target_dir} ...")
    shutil.copytree(
        file_to_copy,
        target_dir / file_to_copy.name,
    )

    LOGGER.info("finished")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="{levelname: <7} | {asctime} [{name}] {message}",
        style="{",
        stream=sys.stdout,
    )
    build()
