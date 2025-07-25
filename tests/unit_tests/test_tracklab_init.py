import os
import tempfile

import pytest
import tracklab


def test_no_root_dir_access__uses_temp_dir(tmp_path, monkeypatch):
    temp_dir = tempfile.gettempdir()
    root_dir = tmp_path / "create_dir_test"
    os.makedirs(root_dir, exist_ok=True)

    monkeypatch.setattr(
        os,
        "access",
        lambda path, mode: not (
            mode == (os.R_OK | os.W_OK) and str(path) == str(root_dir)
        ),
    )

    with tracklab.init(dir=root_dir) as run:
        run.log({"test": 1})

    assert run.settings.root_dir == temp_dir


def test_no_temp_dir_access__throws_error(monkeypatch):
    monkeypatch.setattr(os, "access", lambda path, mode: False)

    temp_dir = tempfile.gettempdir()
    monkeypatch.setattr(
        os,
        "access",
        lambda path, mode: not (
            mode == (os.R_OK | os.W_OK) and str(path) == str(temp_dir)
        ),
    )

    with pytest.raises(ValueError):
        with tracklab.init(dir=temp_dir) as run:
            run.log({"test": 1})


def test_makedirs_raises_oserror__uses_temp_dir(tmp_path, monkeypatch):
    tmp_file = tmp_path / "test.txt"
    tmp_file.touch()

    with tracklab.init(dir=str(tmp_file / "dir2")) as run:
        run.log({"test": 1})

    assert run.settings.root_dir == tempfile.gettempdir()
