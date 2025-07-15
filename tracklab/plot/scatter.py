from __future__ import annotations

from typing import TYPE_CHECKING

from tracklab.plot.custom_chart import plot_table

if TYPE_CHECKING:
    import tracklab
    from tracklab.plot.custom_chart import CustomChart


def scatter(
    table: tracklab.Table,
    x: str,
    y: str,
    title: str = "",
    split_table: bool = False,
) -> CustomChart:
    """Constructs a scatter plot from a tracklab.Table of data.

    Args:
        table: The W&B Table containing the data to visualize.
        x: The name of the column used for the x-axis.
        y: The name of the column used for the y-axis.
        title: The title of the scatter chart.
        split_table: Whether the table should be split into a separate section
            in the W&B UI. If `True`, the table will be displayed in a section named
            "Custom Chart Tables". Default is `False`.

    Returns:
        CustomChart: A custom chart object that can be logged to W&B. To log the
            chart, pass it to `tracklab.log()`.
    Example:
    ```python
    import math
    import random
    import tracklab

    # Simulate temperature variations at different altitudes over time
    data = [
        [i, random.uniform(-10, 20) - 0.005 * i + 5 * math.sin(i / 50)]
        for i in range(300)
    ]

    # Create W&B table with altitude (m) and temperature (°C) columns
    table = tracklab.Table(data=data, columns=["altitude (m)", "temperature (°C)"])

    # Initialize W&B run and log the scatter plot
    with tracklab.init(project="temperature-altitude-scatter") as run:
        # Create and log the scatter plot
        scatter_plot = tracklab.plot.scatter(
            table=table,
            x="altitude (m)",
            y="temperature (°C)",
            title="Altitude vs Temperature",
        )
        run.log({"altitude-temperature-scatter": scatter_plot})
    ```
    """
    return plot_table(
        data_table=table,
        vega_spec_name="wandb/scatter/v0",
        fields={"x": x, "y": y},
        string_fields={"title": title},
        split_table=split_table,
    )
