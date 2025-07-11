from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
import tracklab

if TYPE_CHECKING:
    from tracklab.plot.custom_chart import CustomChart


@pytest.fixture
def roc_curve() -> CustomChart:
    return tracklab.plot.roc_curve(
        y_true=[0, 1],
        y_probas=[
            (0.4, 0.6),
            (0.3, 0.7),
        ],
        title="New title",
    )


@pytest.fixture
def line_series() -> CustomChart:
    return tracklab.plot.line_series(
        xs=[0, 1, 2, 3, 4],
        ys=[[123, 333, 111, 42, 533]],
        keys=["metric_A"],
    )


@pytest.fixture
def confusion_matrix() -> CustomChart:
    return tracklab.plot.confusion_matrix(
        y_true=[0, 1],
        probs=[
            (0.4, 0.6),
            (0.2, 0.8),
        ],
    )


@pytest.fixture
def bar_chart() -> CustomChart:
    return tracklab.plot.bar(
        table=tracklab.Table(columns=["a"], data=[[1]]),
        label="a",
        value="a",
    )


@pytest.fixture
def histogram() -> CustomChart:
    return tracklab.plot.histogram(table=tracklab.Table(columns=["a"], data=[[1]]), value="a")


@pytest.fixture
def line_chart() -> CustomChart:
    return tracklab.plot.line(
        table=tracklab.Table(columns=["a"], data=[[1]]),
        x=[0, 1, 2, 3, 4],
        y=[[1, 2, 3, 4, 5]],
    )


@pytest.fixture
def pr_curve() -> CustomChart:
    return tracklab.plot.pr_curve(
        y_true=[0, 1],
        y_probas=[
            (0.4, 0.6),
            (0.3, 0.7),
        ],
    )


@pytest.fixture
def scatter_plot() -> CustomChart:
    return tracklab.plot.scatter(
        table=tracklab.Table(columns=["a"], data=[[1]]),
        x=[1, 2, 3],
        y=[4, 5, 6],
    )


def get_table_from_summary(run, summary: dict, key_path: list[str]) -> tracklab.Table:
    table_path = summary
    for key in key_path:
        table_path = table_path[key]
    table_path = table_path["path"]
    table_path = f"{run.dir}/{table_path}"
    table_json = json.load(open(table_path))
    return tracklab.Table(data=table_json["data"], columns=table_json["columns"])


@pytest.mark.parametrize(
    "plot_object",
    [
        "line_series",
        "roc_curve",
        "confusion_matrix",
        "bar_chart",
        "histogram",
        "line_chart",
        "pr_curve",
        "scatter_plot",
    ],
)
def test_log_nested_plot(user, request, wandb_backend_spy, plot_object):
    plot = request.getfixturevalue(plot_object)
    with tracklab.init() as run:
        run.log(
            {
                "layer1": {
                    "layer2": {"layer3": plot},
                }
            }
        )

    with wandb_backend_spy.freeze() as snapshot:
        summary = snapshot.summary(run_id=run.id)

        # Verify the table was set in the config and summary
        assert "layer1.layer2.layer3_table" in summary

        table = get_table_from_summary(run, summary, ["layer1.layer2.layer3_table"])
        assert table == plot.table


def test_log_multiple_nested_plots(user, wandb_backend_spy):
    with tracklab.init() as run:
        plot1 = tracklab.plot.line_series(
            xs=[0, 1, 2, 3, 4],
            ys=[[123, 333, 111, 42, 533]],
            keys=["metric_A"],
        )
        plot2 = tracklab.plot.roc_curve(
            y_true=[0, 1],
            y_probas=[
                (0.4, 0.6),
                (0.3, 0.7),
            ],
            title="New title",
        )

        run.log(
            {
                "layer1": {
                    "layer2": {"layer3": plot1},
                    "layer4": {"layer5": plot2},
                }
            }
        )

    with wandb_backend_spy.freeze() as snapshot:
        summary = snapshot.summary(run_id=run.id)
        config = snapshot.config(run_id=run.id)

        # Verify the table was set in the config and summary
        assert "layer1.layer2.layer3_table" in summary
        assert "layer1.layer2.layer3" in config["_wandb"]["value"]["visualize"]

        assert "layer1.layer4.layer5_table" in summary
        assert "layer1.layer4.layer5" in config["_wandb"]["value"]["visualize"]

        for plot, key_path in [
            (plot1, ["layer1.layer2.layer3_table"]),
            (plot2, ["layer1.layer4.layer5_table"]),
        ]:
            table = get_table_from_summary(run, summary, key_path)
            assert table == plot.table


def test_log_nested_table(user, wandb_backend_spy):
    with tracklab.init() as run:
        table1 = tracklab.Table(columns=["a"], data=[[1]])
        table2 = tracklab.Table(columns=["b"], data=[[2]])
        run.log(
            {
                "layer1": {
                    "layer2": {"layer3": table1},
                    "layer4": {"layer5": table2},
                }
            }
        )

    with wandb_backend_spy.freeze() as snapshot:
        summary = snapshot.summary(run_id=run.id)

        assert "layer3" in summary["layer1"]["layer2"]
        assert "layer5" in summary["layer1"]["layer4"]

        for expected_table, key_path in [
            (table1, ["layer1", "layer2", "layer3"]),
            (table2, ["layer1", "layer4", "layer5"]),
        ]:
            summary_table = get_table_from_summary(run, summary, key_path)
            assert expected_table == summary_table


def test_log_nested_visualize(user, wandb_backend_spy):
    with tracklab.init() as run:
        table1 = tracklab.Table(columns=["a"], data=[[1]])
        table2 = tracklab.Table(columns=["b"], data=[[2]])

        visualize1 = tracklab.visualize(
            "wandb/confusion_matrix/v1",
            table1,
        )
        visualize2 = tracklab.visualize(
            "wandb/confusion_matrix/v1",
            table2,
        )
        run.log(
            {
                "layer1": {
                    "layer2": {"layer3": visualize1},
                    "layer4": {"layer5": visualize2},
                }
            }
        )

    with wandb_backend_spy.freeze() as snapshot:
        summary = snapshot.summary(run_id=run.id)

        assert "layer1.layer2.layer3" in summary
        assert "layer1.layer4.layer5" in summary

        for visualize, key_path in [
            (visualize1, ["layer1.layer2.layer3"]),
            (visualize2, ["layer1.layer4.layer5"]),
        ]:
            table = get_table_from_summary(run, summary, key_path)
            assert table == visualize.table
