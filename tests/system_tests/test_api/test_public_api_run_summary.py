import pytest
import tracklab


def test_delete_summary_metric_w_no_lazyload(user):
    with tracklab.init(project="test") as run:
        run_id = run.id

        metric = "test_val"
        for i in range(10):
            run.log({metric: i})

    run = tracklab.Api().run(f"test/{run_id}")
    del run.summary[metric]
    run.update()

    # pytest.raises to expect a KeyError when accessing the deleted metric
    with pytest.raises(KeyError):
        _ = run.summary[metric]
