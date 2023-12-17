import logging
import shutil
from pathlib import Path
from typing import Optional

import pytest

from pythonning.filesystem import move_directory_content
from pythonning.filesystem import get_dir_content
from pythonning.filesystem import copytree
from pythonning.filesystem import copyfile


LOGGER = logging.getLogger(__name__)


def test_move_directory_content(tmp_path: Path, data_root_dir: Path):
    src_copy_dir = data_root_dir / "movedircontent01"
    dst_copy_dir = tmp_path / "src"
    shutil.copytree(src_copy_dir, dst_copy_dir)

    test_src_dir = dst_copy_dir
    test_dst_dir = tmp_path / "dst"

    with pytest.raises(FileNotFoundError):
        move_directory_content(
            test_src_dir, test_dst_dir, exists_ok=False, recursive=False
        )

    test_dst_dir.mkdir()

    move_directory_content(test_src_dir, test_dst_dir, exists_ok=False, recursive=False)
    assert not len(list(test_src_dir.glob("*")))
    assert len(list(test_dst_dir.glob("*"))) == 2
    assert Path(test_dst_dir / "foo.py").exists()
    assert Path(test_dst_dir / "somedir").exists()
    assert Path(test_dst_dir / "somedir" / "file.py").exists()
    assert Path(test_dst_dir / "somedir" / "file.sh").exists()

    dst_copy_dir.rmdir()
    shutil.copytree(src_copy_dir, dst_copy_dir)
    with pytest.raises(FileExistsError):
        move_directory_content(
            test_src_dir, test_dst_dir, exists_ok=False, recursive=False
        )
    assert len(list(test_dst_dir.glob("*"))) == 2

    move_directory_content(test_src_dir, test_dst_dir, exists_ok=True, recursive=False)
    assert len(list(test_dst_dir.glob("*"))) == 2
    assert Path(test_dst_dir / "foo.py").exists()
    assert Path(test_dst_dir / "somedir").exists()
    assert len(list(Path(test_dst_dir / "somedir").glob("*"))) == 2
    assert Path(test_dst_dir / "somedir" / "file.py").exists()
    assert Path(test_dst_dir / "somedir" / "file.sh").exists()


def test_move_directory_content_recursive(tmp_path: Path, data_root_dir: Path):
    src_copy01_dir = data_root_dir / "movedircontent01"
    dst_copy01_dir = tmp_path / "src01"
    shutil.copytree(src_copy01_dir, dst_copy01_dir)

    src_copy02_dir = data_root_dir / "movedircontent02"
    dst_copy02_dir = tmp_path / "src02"
    shutil.copytree(src_copy02_dir, dst_copy02_dir)

    test_src_dir = dst_copy01_dir
    test_dst_dir = tmp_path / "dst"
    test_dst_dir.mkdir()

    move_directory_content(test_src_dir, test_dst_dir, exists_ok=False, recursive=False)

    test_src_dir = dst_copy02_dir
    move_directory_content(test_src_dir, test_dst_dir, exists_ok=True, recursive=False)
    assert len(list(test_dst_dir.glob("*"))) == 2
    assert Path(test_dst_dir / "foo.py").exists()
    assert Path(test_dst_dir / "somedir").exists()
    assert len(list(Path(test_dst_dir / "somedir").glob("*"))) == 2
    assert Path(test_dst_dir / "somedir" / "file.py").exists()
    assert Path(test_dst_dir / "somedir" / "file.sh").exists()

    # directory is not empty because we didnt use recursive=True
    with pytest.raises(OSError):
        dst_copy02_dir.rmdir()

    dst_copy03_dir = tmp_path / "src03"
    shutil.copytree(src_copy02_dir, dst_copy03_dir)
    test_src_dir = dst_copy03_dir
    move_directory_content(test_src_dir, test_dst_dir, exists_ok=True, recursive=True)
    assert len(list(test_dst_dir.glob("*"))) == 2
    assert Path(test_dst_dir / "foo.py").exists()
    assert Path(test_dst_dir / "somedir").exists()
    assert len(list(Path(test_dst_dir / "somedir").glob("*"))) == 3
    assert Path(test_dst_dir / "somedir" / "file.py").exists()
    assert Path(test_dst_dir / "somedir" / "file.sh").exists()
    assert Path(test_dst_dir / "somedir" / "NEWFILE").exists()


def test_get_dir_content(data_root_dir: Path):
    src_dir = data_root_dir / "getdircontent01"

    result = get_dir_content(src_dir, recursive=False)
    assert len(result) == 2

    result = get_dir_content(src_dir, recursive=True)
    assert len(result) == 11, str(list(map(str, result)))


class _Progress:
    def __init__(self):
        self.current: int = 0
        self.total: Optional[int] = None

    def next(self):
        self.current += 1


def test_copytree(tmp_path: Path, data_root_dir: Path):
    src_dir = data_root_dir / "copytree01"
    dst_copy01_dir = tmp_path / "src01"

    expected_paths = [
        src_dir / "assets",
        src_dir / "assets" / "table01",
        src_dir / "assets" / "table01" / "model",
        src_dir / "assets" / "table01" / "model" / "model.txt",
        src_dir / "assets" / "table01" / "surfacing",
        src_dir / "assets" / "table01" / "surfacing" / "texture_albedo.txt",
        src_dir / "assets" / "table01" / "surfacing" / "texture_normal.txt",
        src_dir / "assets" / "table01" / "surfacing" / "texture_specular_roughness.txt",
        src_dir / "assets" / "table01" / "data.json",
        src_dir / "assets" / "README.md",
        src_dir / "README.md",
    ]
    expected_paths.sort()

    progress = _Progress()
    paths = []

    def callback(path, index, total):
        progress.next()
        progress.total = total
        paths.append(path)

    copytree(src_dir, dst_copy01_dir, callback=callback)

    assert progress.current == 11
    assert progress.total == 11
    paths.sort()
    assert expected_paths == paths


def test_copyfile(tmp_path: Path, data_root_dir: Path):
    src_text_file = data_root_dir / "copyfile" / "text.txt"
    src_render_file = data_root_dir / "copyfile" / "render.jpg"
    dst_copy01_dir = tmp_path / "dst01"
    dst_copy01_dir.mkdir()
    dst_copy02_dir = tmp_path / "dst02"
    dst_copy02_dir.mkdir()

    progress = []
    totals = []
    chunk_sizes = []

    def _callback(chunk, chunk_size, total):
        progress.append(chunk)
        chunk_sizes.append(chunk_size)
        totals.append(total)

    dst_file = dst_copy01_dir / src_text_file.name
    assert not dst_file.exists()
    copyfile(src_text_file, dst_copy01_dir, callback=_callback)
    assert dst_file.exists()
    # txt is a small file so only had one call
    assert len(progress) == 1
    assert totals[-1] == 3371

    dst_file = dst_copy01_dir / "success.py"
    assert not dst_file.exists()
    copyfile(src_text_file, dst_file, callback=_callback)
    assert dst_file.exists()

    progress = []
    totals = []
    chunk_sizes = []

    dst_file = dst_copy02_dir / src_render_file.name
    assert not dst_file.exists()
    copyfile(src_render_file, dst_copy02_dir, callback=_callback, chunk_size=280000)
    assert dst_file.exists()

    assert len(progress) == 7
    assert totals[-1] == 1685626, totals
    assert chunk_sizes[-1] == 280000
