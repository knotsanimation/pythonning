import logging
import os
import sys
from pathlib import Path

import rezbuild_utils

LOGGER = logging.getLogger(__name__)


def build():
    if not os.getenv("REZ_BUILD_INSTALL") == "1":
        LOGGER.info(f"skipped")
        return

    rezbuild_utils.copy_build_files(
        [
            Path("python"),
        ]
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
