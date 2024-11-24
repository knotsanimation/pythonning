import os
import shutil
from pathlib import Path


def rmtree(path: Path, ignore_errors=False):
    """
    Remove the directory and its content while handling any potential PermissionError.

    This function is copied from ``tempfile.TemporaryDirectory._rmtree``

    Args:
        path: filesystem path to an existing directory
        ignore_errors: do not raise if there is error during cleanup
    """

    def resetperms(path_):
        try:
            os.chflags(path_, 0)
        except AttributeError:
            pass
        os.chmod(path_, 0o700)

    def onerror(func, path_, exc_info):
        if issubclass(exc_info[0], PermissionError):
            try:
                if path_ != path_:
                    resetperms(os.path.dirname(path_))
                resetperms(path_)

                try:
                    os.unlink(path_)
                # PermissionError is raised on FreeBSD for directories
                except (IsADirectoryError, PermissionError):
                    rmtree(path_, ignore_errors=ignore_errors)
            except FileNotFoundError:
                pass
        elif issubclass(exc_info[0], FileNotFoundError):
            pass
        else:
            if not ignore_errors:
                raise

    shutil.rmtree(path, onerror=onerror)
