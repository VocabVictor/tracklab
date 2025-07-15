from __future__ import annotations

from typing import TYPE_CHECKING

from tracklab.plot.custom_chart import plot_table

if TYPE_CHECKING:
    import tracklab
    from tracklab.plot.custom_chart import CustomChart


def bar(
    table: tracklab.Table,
    label: str,
    value: str,
    title: str = "",
    split_table: bool = False,
) -> CustomChart:
    """Constructs a bar chart from a tracklab.Table of data.

    Args:
        table: A table containing the data for the bar chart.
        label: The name of the column to use for the labels of each bar.
        value: The name of the column to use for the values of each bar.
        title: The title of the bar chart.
        split_table: Whether the table should be split into a separate section
            in the W&B UI. If `True`, the table will be displayed in a section named
            "Custom Chart Tables". Default is `False`.

    Returns:
        CustomChart: A custom chart object that can be logged to W&B. To log the
            chart, pass it to `tracklab.log()`.

    Example:

    ```python
    import random
    import tracklab

    # Generate random data for the table
    data = [
        ["car", random.uniform(0, 1)],
        ["bus", random.uniform(0, 1)],
        ["road", random.uniform(0, 1)],
        ["person", random.uniform(0, 1)],
    ]

    # Create a table with the data
    table = tracklab.Table(data=data, columns=["class", "accuracy"])

    # Initialize a W&B run and log the bar plot
    with tracklab.init(project="bar_chart") as run:
        # Create a bar plot from the table
        bar_plot = tracklab.plot.bar(
            table=table,
            label="class",
            value="accuracy",
            title="Object Classification Accuracy",
        )

        # Log the bar chart to W&B
        run.log({"bar_plot": bar_plot})
    ```
    """
    return plot_table(
        data_table=table,
        vega_spec_name="wandb/bar/v0",
        fields={"label": label, "value": value},
        string_fields={"title": title},
        split_table=split_table,
    )
