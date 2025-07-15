"""require user tests."""

import pytest
import tracklab


@pytest.fixture
def mock_require(mocker):
    cleanup = []

    def fn(require, func):
        cleanup.append(require)
        mocker.patch.object(
            tracklab.sdk.wandb_require._Requires,
            "require_" + require,
            func,
            create=True,
        )

    yield fn
    for require in cleanup:
        tracklab.__dict__.pop("require_" + require, None)


def test_require_single(capsys):
    with pytest.raises(tracklab.errors.UnsupportedError):
        tracklab.require("something")
    captured = capsys.readouterr()
    assert "unsupported requirement: something" in captured.err


def test_require_list(capsys):
    with pytest.raises(tracklab.errors.UnsupportedError):
        tracklab.require(["something", "another"])
    captured = capsys.readouterr()
    assert "unsupported requirement: something" in captured.err
    assert "unsupported requirement: another" in captured.err


def test_require_version(capsys):
    with pytest.raises(tracklab.errors.UnsupportedError):
        tracklab.require("something@beta")
    captured = capsys.readouterr()
    assert "unsupported requirement: something" in captured.err


def test_require_param(capsys):
    with pytest.raises(tracklab.errors.UnsupportedError):
        tracklab.require("something:param@beta")
    captured = capsys.readouterr()
    assert "unsupported requirement: something" in captured.err


def test_require_good(mock_require):
    def mock_require_test(self):
        tracklab.require_test = lambda x: x + 2

    mock_require("test", mock_require_test)
    tracklab.require("test")

    assert tracklab.require_test(2) == 4


@pytest.mark.usefixtures("mock_require")
def test_require_require():
    # This is a noop now that it is "released"
    tracklab.require("require")
