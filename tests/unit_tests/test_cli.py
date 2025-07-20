import datetime
import getpass
import importlib
import netrc
import os
import subprocess
import traceback
from unittest import mock

import pytest
import tracklab
from tracklab.cli import cli


def get_netrc_file_path():
    return "/tmp/tracklab_netrc"


@pytest.fixture
def empty_netrc(monkeypatch):
    class FakeNet:
        @property
        def hosts(self):
            return {"api.tracklab.ai": None}

    monkeypatch.setattr(netrc, "netrc", lambda *args: FakeNet())


@pytest.mark.skip(reason="Currently dont have on in cling")
def test_enable_on(runner, git_repo):
    with runner.isolated_filesystem():
        with open("wandb/settings", "w") as f:
            f.write("[default]\nproject=rad")
        result = runner.invoke(cli.on)
        assert "W&B enabled" in str(result.output)
        assert result.exit_code == 0


@pytest.mark.skip(reason="Currently dont have off in cling")
def test_enable_off(runner, git_repo):
    with runner.isolated_filesystem():
        with open("wandb/settings", "w") as f:
            f.write("[default]\nproject=rad")
        result = runner.invoke(cli.off)
        assert "W&B disabled" in str(result.output)
        assert "disabled" in open("wandb/settings").read()
        assert result.exit_code == 0


def test_no_project_bad_command(runner):
    with runner.isolated_filesystem():
        result = runner.invoke(cli.cli, ["fsd"])
        assert "No such command" in result.output
        assert result.exit_code == 2


@pytest.mark.skip(reason="sync command removed in local-only mode")
def test_sync_gc(runner):
    """Test was for sync command which is not available in local-only mode."""
    pass


def test_cli_debug_log_scoping(runner, test_settings):
    with runner.isolated_filesystem():
        os.chdir(os.getcwd())
        for test_user in ("user1", "user2"):
            with mock.patch("getpass.getuser", return_value=test_user):
                importlib.reload(cli)
                assert cli._username == test_user
                assert cli._tracklab_log_path.endswith(f"debug-cli.{test_user}.log")