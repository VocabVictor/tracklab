import os
from unittest import mock

from tracklab.old.settings import Settings


def test__global_path_default_exists_and_is_writable():
    home_dir = os.path.expanduser("~")
    assert Settings._global_path() == os.path.join(
        home_dir, ".config", "wandb", "settings"
    )


def test__global_path_default_does_not_exist_and_is_not_writable():
    with mock.patch("os.makedirs") as mock_makedirs, mock.patch(
        "os.access", return_value=True
    ), mock.patch("tempfile.gettempdir", return_value="/tmp"), mock.patch(
        "getpass.getuser", return_value="testuser"
    ):
        mock_makedirs.side_effect = [OSError, True]
        assert Settings._global_path() == os.path.join(
            "/tmp", ".config", "wandb", "settings"
        )

        mock_makedirs.side_effect = OSError
        assert Settings._global_path() == os.path.join(
            "/tmp", "testuser", ".config", "wandb", "settings"
        )


def test__global_path_env_var_exists_and_is_writable(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    monkeypatch.setenv("TRACKLAB_CONFIG_DIR", config_dir)

    settings_path = Settings._global_path()

    assert settings_path == os.path.join(config_dir, "settings")
    assert os.path.exists(config_dir)
