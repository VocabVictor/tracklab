import pickle
import tempfile

import pytest
import tracklab

def test_mode_disabled():
    """Test that the user can access all attributes of a Run object (TrackLab is now local-only)."""
    run = tracklab.init()
    symbols = [s for s in dir(run) if not s.startswith("_") and s != "log"]

    # try logging some stuff
    run.log({"a": 1})

    for symbol in symbols:
        # try accessing the attribute
        getattr(run, symbol)
        if callable(getattr(run, symbol)):
            # try calling the method
            getattr(run, symbol)()

    # disabled mode should not allow referencing attributes that don't exist
    with pytest.raises(AttributeError):
        assert run.here_s_a_twist_i_dont_exist

    with pytest.raises(AttributeError):
        assert run.me_too()

def test_disabled_can_pickle():
    # This case comes up when using tracklab locally, with keras
    run = tracklab.init()

    with tempfile.NamedTemporaryFile() as temp_file:
        pickle.dump(run, temp_file)

def test_disabled_context_manager():
    with tracklab.init() as run:
        run.log({"a": 1})
        run.summary.update({"b": 2})
        run.config.update({"c": 3})
    # run.log_artifact("artifact") # Artifact test removed
    # run.use_artifact("artifact") # Artifact test removed
        run.log_model("model")
        run.use_model("model")
        run.link_model("model")
        run.define_metric("metric")
        run.mark_preempting()
        run.alert("alert")
