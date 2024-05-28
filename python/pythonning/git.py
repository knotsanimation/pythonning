"""
perhaps worth to create its own package for it, but good here as long as it doesn't
grow too big.

Of course all the commands assume git is installed on the system and can be accessed
by calling ``git`` in the terminal.
"""
import logging
import subprocess
from pathlib import Path
from typing import List

LOGGER = logging.getLogger(__name__)


def _call_git(git_args: List[str], cwd: Path = None) -> str:
    """
    Call a git command in the terminal and return its output as a decoded string.

    Args:
        git_args: list of argument to pass to git.
        cwd: current working directory, usually root of the git repository.

    Returns:
        output of the git command
    """
    command = ["git"] + git_args
    commit = subprocess.check_output(command, cwd=cwd)
    # XXX: is the rstrip safe in all cases ?
    return commit.decode("utf-8").rstrip("\n")


def get_current_commit_hash(repository_path: Path = None) -> str:
    """
    Return the hash of the latest commit the repository is currently at.

    Args:
        repository_path:
            optional filesysten path to an existing directory,
            use current working directory (cwd) if not provided.
    """
    return _call_git(["rev-parse", "HEAD"], cwd=repository_path)
