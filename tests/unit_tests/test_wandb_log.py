import pytest
import tracklab

# ----------------------------------
# tracklab.log
# ----------------------------------


def test_nice_log_error():
    with pytest.raises(tracklab.Error):
        tracklab.log({"no": "init"})


def test_nice_log_error_config():
    with pytest.raises(
        tracklab.Error, match=r"You must call tracklab.init\(\) before tracklab.config.update"
    ):
        tracklab.config.update({"foo": 1})
    with pytest.raises(
        tracklab.Error, match=r"You must call tracklab.init\(\) before tracklab.config.foo"
    ):
        tracklab.config.foo = 1


def test_nice_log_error_summary():
    with pytest.raises(
        tracklab.Error,
        match=r"You must call tracklab.init\(\) before tracklab.summary\['great'\]",
    ):
        tracklab.summary["great"] = 1
    with pytest.raises(
        tracklab.Error, match=r"You must call tracklab.init\(\) before tracklab.summary.bam"
    ):
        tracklab.summary.bam = 1


def test_log_only_strings_as_keys(mock_run):
    run = mock_run()
    with pytest.raises(TypeError):
        run.log({1: 1000})
    with pytest.raises(TypeError):
        run.log({("tup", "idx"): 1000})


def test_log_not_dict(mock_run):
    run = mock_run()
    with pytest.raises(TypeError):
        run.log(10)
