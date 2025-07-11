from unittest import mock

import pytest
import tracklab


@pytest.mark.parametrize("verify", [None, True])
def test_login_valid_key(user, verify):
    logged_in = tracklab.login(verify=verify)
    assert logged_in


def test_login_invalid_key(user):
    with mock.patch.dict("os.environ", {"WANDB_API_KEY": "I" * 40}):
        with pytest.raises(tracklab.errors.AuthenticationError):
            tracklab.login(verify=True)


def test_login_invalid_key_no_verify(user):
    with mock.patch.dict("os.environ", {"WANDB_API_KEY": "I" * 40}):
        logged_in = tracklab.login(verify=False)
        assert logged_in


def test_login_invalid_key_length(user):
    with mock.patch.dict("os.environ", {"WANDB_API_KEY": ""}):
        with pytest.raises(tracklab.errors.AuthenticationError):
            tracklab.login(verify=True, key="I")
        assert tracklab.api.api_key is None
