import json
import os
import platform
import queue
import sys
import tempfile
import threading
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import pytest
import tracklab
from tracklab.sdk.lib.credentials import _expires_at_fmt


@pytest.fixture
def mock_tty(monkeypatch):
    class WriteThread(threading.Thread):
        def __init__(self, fname):
            threading.Thread.__init__(self)
            self._fname = fname
            self._q = queue.Queue()

        def run(self):
            with open(self._fname, "w") as fp:
                while True:
                    data = self._q.get()
                    if data == "_DONE_":
                        break
                    fp.write(data)
                    fp.flush()

        def add(self, input_str):
            self._q.put(input_str)

        def stop(self):
            self.add("_DONE_")

    with tempfile.TemporaryDirectory() as tmpdir:
        fds = dict()

        def setup_fn(input_str):
            fname = os.path.join(tmpdir, "file.txt")
            if platform.system() != "Windows":
                os.mkfifo(fname, 0o600)
                writer = WriteThread(fname)
                writer.start()
                writer.add(input_str)
                fds["writer"] = writer
                monkeypatch.setattr("termios.tcflush", lambda x, y: None)
            else:
                # windows doesn't support named pipes, just write it
                # TODO: emulate msvcrt to support input on windows
                with open(fname, "w") as fp:
                    fp.write(input_str)
            fds["stdin"] = open(fname)
            monkeypatch.setattr("sys.stdin", fds["stdin"])
            sys.stdin.isatty = lambda: True
            sys.stdout.isatty = lambda: True

        yield setup_fn

        writer = fds.get("writer")
        if writer:
            writer.stop()
            writer.join()
        stdin = fds.get("stdin")
        if stdin:
            stdin.close()

    del sys.stdin.isatty
    del sys.stdout.isatty


def test_login_timeout(mock_tty):
    mock_tty("junk\nmore\n")
    ret = tracklab.login(timeout=4)
    assert ret is False
    assert tracklab.api.api_key is None
    assert tracklab.setup().settings.mode == "disabled"


@pytest.mark.skipif(
    platform.system() == "Windows",
    reason="mock_tty does not support windows input yet",
)
def test_login_timeout_choose(mock_tty):
    mock_tty("3\n")
    ret = tracklab.login(timeout=8)
    assert ret is False
    assert tracklab.api.api_key is None
    assert tracklab.setup().settings.mode == "offline"


def test_login_timeout_env_blank(mock_tty):
    mock_tty("\n\n\n")
    with mock.patch.dict(os.environ, {"WANDB_LOGIN_TIMEOUT": "4"}):
        ret = tracklab.login()
        assert ret is False
        assert tracklab.api.api_key is None
        assert tracklab.setup().settings.mode == "disabled"


def test_login_timeout_env_invalid(mock_tty):
    mock_tty("")
    with mock.patch.dict(os.environ, {"WANDB_LOGIN_TIMEOUT": "junk"}):
        with pytest.raises(ValueError):
            tracklab.login()


def test_relogin_timeout(dummy_api_key):
    logged_in = tracklab.login(relogin=True, key=dummy_api_key)
    assert logged_in is True
    logged_in = tracklab.login()
    assert logged_in is True


def test_login_key(capsys):
    tracklab.login(key="A" * 40)
    # TODO: this was a bug when tests were leaking out to the global config
    # tracklab.api.set_setting("base_url", "http://localhost:8080")
    _, err = capsys.readouterr()
    assert "Appending key" in err
    #  WTF is happening?
    assert tracklab.api.api_key == "A" * 40


def test_login(test_settings):
    settings = test_settings(dict(mode="disabled"))
    tracklab.setup(settings=settings)
    tracklab.login()
    tracklab.finish()


def test_login_anonymous():
    with mock.patch.dict("os.environ", WANDB_API_KEY="ANONYMOOSE" * 4):
        tracklab.login(anonymous="must")
        assert tracklab.api.api_key == "ANONYMOOSE" * 4
        assert tracklab.setup().settings.anonymous == "must"


def test_login_sets_api_base_url(local_settings):
    with mock.patch.dict("os.environ", WANDB_API_KEY="ANONYMOOSE" * 4):
        base_url = "https://api.test.host.ai"
        tracklab.login(anonymous="must", host=base_url)
        api = tracklab.Api()
        assert api.settings["base_url"] == base_url
        base_url = "https://api.tracklab.ai"
        tracklab.login(anonymous="must", host=base_url)
        api = tracklab.Api()
        assert api.settings["base_url"] == base_url


def test_login_invalid_key():
    with mock.patch(
        "tracklab.apis.internal.Api.validate_api_key",
        return_value=False,
    ):
        tracklab.ensure_configured()
        with pytest.raises(tracklab.errors.AuthenticationError):
            tracklab.login(key="X" * 40, verify=True)

        assert tracklab.api.api_key is None


def test_login_with_token_file(tmp_path: Path):
    token_file = str(tmp_path / "jwt.txt")
    credentials_file = str(tmp_path / "credentials.json")
    base_url = "https://api.tracklab.ai"

    with open(token_file, "w") as f:
        f.write("eyaksdcmlasfm")

    expires_at = datetime.now() + timedelta(days=5)
    data = {
        "credentials": {
            base_url: {
                "access_token": "wb_at_ksdfmlaskfm",
                "expires_at": expires_at.strftime(_expires_at_fmt),
            }
        }
    }
    with open(credentials_file, "w") as f:
        json.dump(data, f)

    with mock.patch.dict(
        "os.environ",
        WANDB_IDENTITY_TOKEN_FILE=token_file,
        WANDB_CREDENTIALS_FILE=credentials_file,
    ):
        tracklab.login()
        assert tracklab.api.is_authenticated
