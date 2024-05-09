"""
A script that allow to bump the multiple versions definitions across the project, with the same value.

To use as a CLI like ``python upgrade-version.py 0.1.0`` or interactively like
``python upgrade-version.py``.
"""
import argparse
import logging
import sys
from pathlib import Path

LOGGER = logging.getLogger(__name__)

THISDIR = Path(__file__).parent.resolve()


def get_cli(argv=None):
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser("upgrade-version")
    parser.add_argument("version", type=str, help="A semver version to set like 0.1.0")
    parsed = parser.parse_args(argv)
    return parsed


def _replace_line_in_file(file_path: Path, line_starts: str, new_version: str):
    LOGGER.info(f"reading {file_path}")
    current_content = file_path.read_text(encoding="utf-8").split("\n")

    for line_index, line in enumerate(current_content):
        if line.startswith(line_starts):
            line_version_index = line_index
            break
    else:
        raise RuntimeError("Could not find version in __init__.py")

    new_content = list(current_content)
    current_version = new_content.pop(line_version_index)
    new_version = f"{line_starts}{new_version}"
    LOGGER.info(f"replacing current version '{current_version}' with '{new_version}'")
    new_content.insert(line_version_index, new_version)

    new_content = "\n".join(new_content)
    LOGGER.info(f"writing to {file_path}")
    file_path.write_text(new_content, encoding="utf-8")


def main():
    if sys.argv[1:]:
        cli = get_cli()
        version = cli.version
    else:
        version = input("new version:")

    package_init_path = THISDIR / "python" / "pythonning" / "__init__.py"
    _replace_line_in_file(
        file_path=package_init_path,
        line_starts="__version__ =",
        new_version=f' "{version}"',
    )

    package_path = THISDIR / "package.py"
    _replace_line_in_file(
        file_path=package_path,
        line_starts="version =",
        new_version=f' "{version}"',
    )

    setup_path = THISDIR / "setup.py"
    _replace_line_in_file(
        file_path=setup_path,
        line_starts="    version=",
        new_version=f'"{version}",',
    )
    LOGGER.info("finished")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="{levelname: <7} | {asctime} [{name}] {message}",
        style="{",
        stream=sys.stdout,
    )
    main()
