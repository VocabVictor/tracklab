import pytest
import tracklab
from tracklab.errors import UsageError


def test_profiler_without_init():
    pytest.importorskip("torch")
    import torch

    with pytest.raises(UsageError) as e_info:
        with torch.profiler.profile(
            schedule=torch.profiler.schedule(wait=1, warmup=1, active=3, repeat=1),
            on_trace_ready=tracklab.profiler.torch_trace_handler(),
            record_shapes=True,
            with_stack=True,
        ) as prof:
            prof.step()
        assert (
            str(e_info.value)
            == "Please call tracklab.init() before tracklab.profiler.trace()"
        )
