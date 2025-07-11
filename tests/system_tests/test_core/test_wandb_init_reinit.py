"""Tests for the `reinit` setting."""

import pytest
import tracklab


def test_reinit_create_new__does_not_modify_wandb_run():
    with tracklab.init(mode="offline", reinit="create_new"):
        assert tracklab.run is None


def test_reinit_default__controls_wandb_run():
    with tracklab.init(mode="offline") as run:
        assert tracklab.run is run

    assert tracklab.run is None


@pytest.mark.parametrize("finish_previous", (True, "finish_previous"))
def test_reinit_finish_previous(finish_previous):
    run1 = tracklab.init(mode="offline")
    run2 = tracklab.init(mode="offline", reinit="create_new")

    tracklab.init(mode="offline", reinit=finish_previous)

    # NOTE: There is no public way to check if a run is finished.
    assert run1._is_finished
    assert run2._is_finished


@pytest.mark.parametrize("return_previous", (False, "return_previous"))
def test_reinit_return_previous(return_previous):
    tracklab.init(mode="offline")
    run2 = tracklab.init(mode="offline", reinit="create_new")
    run3 = tracklab.init(mode="offline", reinit="create_new")

    run3.finish()
    previous = tracklab.init(mode="offline", reinit=return_previous)

    # run2 is returned because it is the most recent unfinished run.
    assert previous is run2
