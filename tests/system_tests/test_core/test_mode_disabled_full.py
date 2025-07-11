"""disabled mode test."""

import os
from unittest import mock

import pytest
import tracklab


def test_disabled_noop(user):
    """Make sure that all objects are dummy objects in noop case."""
    with tracklab.init(mode="disabled") as run:
        run.log(dict(this=2))


def test_disabled_dir(user):
    tmp_dir = "/tmp/dir"
    with mock.patch("tempfile.gettempdir", lambda: tmp_dir):
        run = tracklab.init(mode="disabled")
        assert run.dir == tmp_dir


def test_disabled_summary(user):
    run = tracklab.init(mode="disabled")
    run.summary["cat"] = 2
    run.summary["nested"] = dict(level=3)
    assert "cat" in run.summary
    assert run.summary["cat"] == 2
    assert run.summary.cat == 2
    with pytest.raises(KeyError):
        _ = run.summary["dog"]
    assert run.summary["nested"]["level"] == 3


def test_disabled_globals(user):
    # Test tracklab.* attributes
    run = tracklab.init(config={"foo": {"bar": {"x": "y"}}}, mode="disabled")
    tracklab.log({"x": {"y": "z"}})
    tracklab.log({"foo": {"bar": {"x": "y"}}})
    assert tracklab.run == run
    assert tracklab.config == run.config
    assert tracklab.summary == run.summary
    assert tracklab.config.foo["bar"]["x"] == "y"
    assert tracklab.summary["x"].y == "z"
    assert tracklab.summary["foo"].bar.x == "y"
    tracklab.summary.foo["bar"].update({"a": "b"})
    assert tracklab.summary.foo.bar.a == "b"
    run.finish()


def test_bad_url(user):
    run = tracklab.init(
        settings=dict(mode="disabled", base_url="http://my-localhost:9000")
    )
    run.log({"acc": 0.9})
    run.finish()


def test_no_dirs(user):
    run = tracklab.init(settings={"mode": "disabled"})
    run.log({"acc": 0.9})
    run.finish()
    assert not os.path.isdir("wandb")


def test_access_properties(user):
    run = tracklab.init(mode="disabled")
    assert run.dir
    assert run.disabled
    assert run.entity
    assert run.project == "dummy"
    assert run.project_name() == "dummy"
    assert not run.resumed
    assert run.start_time
    assert run.starting_step == 0
    assert run.step == 0
    assert run.url is None
    assert run.get_url() is None
    assert run.sweep_id is None
    assert run.name
    run.tags = ["tag"]
    assert run.tags == ("tag",)
    assert run.offline is False
    assert run.path
    run.notes = "notes"
    assert run.notes == "notes"
    run.name = "name"
    assert run.name == "name"
    assert run.group == ""
    assert run.job_type == ""
    assert run.config_static

    assert run.project_url is None
    assert run.get_project_url() is None
    assert run.sweep_url is None
    assert run.get_sweep_url() is None

    assert run.status() is None

    run.finish()


def test_disabled_no_activity(wandb_backend_spy):
    gql = wandb_backend_spy.gql
    graphql_spy = gql.Capture()
    wandb_backend_spy.stub_gql(gql.any(), graphql_spy)

    with tracklab.init(settings={"mode": "disabled"}) as run:
        run.alert("alert")
        run.define_metric("metric")
        run.log_code()
        run.save("/lol")
        run.restore()
        run.mark_preempting()
        run.to_html()
        run.display()
    assert graphql_spy.total_calls == 0


def test_disabled_mode_artifact(wandb_backend_spy):
    gql = wandb_backend_spy.gql
    graphql_spy = gql.Capture()
    wandb_backend_spy.stub_gql(gql.any(), graphql_spy)
    run = tracklab.init(settings={"mode": "disabled"})
    art = run.log_artifact(tracklab.Artifact("dummy", "dummy")).wait()
    run.link_artifact(art, "dummy")
    run.finish()
    assert graphql_spy.total_calls == 0
