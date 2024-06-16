import os

from pythonning.web import download_file
from pythonning.web.download import clear_download_cache
from pythonning.web.download import guess_url_filename
from pythonning.web.download import _DOWNLOAD_CACHE
from pythonning.web.download import download_file_smart


def _is_cache_empty() -> bool:
    return _DOWNLOAD_CACHE.is_empty


def test_download_file(tmp_path):
    # we unfortunately need to clear the cache before running the tests
    clear_download_cache()
    assert _is_cache_empty()

    target_file = tmp_path / "githubavatar1"
    assert not target_file.exists()
    assert _is_cache_empty()
    download_file(
        # one day those tests will probably fail because github will change their url :^)
        "https://avatars.githubusercontent.com/u/64362465",
        target_file,
        use_cache=False,
    )
    assert target_file.exists()
    assert _is_cache_empty()

    target_file = tmp_path / "githubavatar2"
    assert not target_file.exists()
    download_file(
        "https://avatars.githubusercontent.com/u/64362465",
        target_file,
        use_cache=True,
    )
    assert target_file.exists()
    assert not _is_cache_empty()

    target_file = tmp_path / "githubavatar3"
    assert not target_file.exists()
    download_file(
        "https://avatars.githubusercontent.com/u/64362465",
        target_file,
        use_cache=True,
    )
    assert target_file.exists()
    assert not _is_cache_empty()

    clear_download_cache()
    assert _is_cache_empty()


class Callback:
    def __init__(self):
        self.progress = 0
        self.total_size = None

    def run(self, block_number, block_size, total_size):
        self.progress += 1
        self.total_size = total_size


def test_download_file_callback(tmp_path):
    clear_download_cache()

    callback = Callback()

    target_file = tmp_path / "githubavatar1"
    assert not target_file.exists()
    download_file(
        # one day those tests will probably fail because github will change their url :^)
        "https://avatars.githubusercontent.com/u/64362465",
        target_file,
        use_cache=False,
        step_callback=callback.run,
    )
    assert target_file.exists()
    assert callback.progress != 0
    # value depends on what is downloaded, here we know it will not be -1
    assert callback.total_size != -1


def test_guess_url_filename():
    filename = guess_url_filename(
        "https://raw.githubusercontent.com/knotsanimation/pythonning/d9d5610ba6aa07235f921c28d9855288a88ba23c/README.md"
    )
    assert filename == "README.md"

    filename = guess_url_filename("https://avatars.githubusercontent.com/u/64362465")
    assert filename == "64362465.jpeg"

    # file stored on my personal google drive
    filename = guess_url_filename(
        "https://drive.usercontent.google.com/download?id=1S0N0ENvzk1SMGSj_15b5ijQPiqkbmwoF&export=download&authuser=0&confirm=t"
    )
    assert filename == "CAlc-D8T-dragon-1024.exr"


def test_download_smart(tmp_path):
    url = "https://drive.usercontent.google.com/download?id=1S0N0ENvzk1SMGSj_15b5ijQPiqkbmwoF&export=download&authuser=0&confirm=t"
    filepath = download_file_smart(url, target_dir=tmp_path)
    assert filepath.exists()
    assert filepath.name == "CAlc-D8T-dragon-1024.exr"
