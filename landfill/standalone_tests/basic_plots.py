import math
import pathlib
import random
import sys

import tracklab


def main(argv):
    # tracklab.init(entity="wandb", project="new-plots-test-5")
    tracklab.init(name=pathlib.Path(__file__).stem)
    data = [[i, random.random() + math.sin(i / 10)] for i in range(100)]
    table = tracklab.Table(data=data, columns=["step", "height"])
    line_plot = tracklab.plot.line(
        table, x="step", y="height", title="what a great line plot"
    )
    xs = []
    ys = []
    keys = [f"y_{i}" for i in range(4)]
    xs.append([j for j in range(100)])
    xs.append([j for j in range(100)])
    xs.append([2 * j for j in range(50)])
    xs.append([2 * j for j in range(50)])

    ys.append([random.random() + math.sin(i / 10) for i in range(100)])
    ys.append([math.sin(i / 10) for i in range(100)])
    ys.append([math.cos(i / 10) for i in range(50)])
    ys.append([random.random() - math.cos(i / 10) for i in range(50)])

    line_series_plot = tracklab.plot.line_series(
        xs, ys, keys, "Get serial With keys now!", "step"
    )
    line_series_plot_no_title_no_keys = tracklab.plot.line_series(xs, ys, xname="step")

    line_series_singular_x_array = tracklab.plot.line_series(
        [i for i in range(100)], ys, title="Get serial with one x", xname="step"
    )

    histogram = tracklab.plot.histogram(table, value="height", title="my-histo")
    scatter = tracklab.plot.scatter(table, x="step", y="height", title="scatter!")

    bar_table = tracklab.Table(
        data=[
            ["car", random.random()],
            ["bus", random.random()],
            ["road", random.random()],
            ["person", random.random()],
            ["cyclist", random.random()],
            ["tree", random.random()],
            ["sky", random.random()],
        ],
        columns=["class", "acc"],
    )
    bar = tracklab.plot.bar(bar_table, label="class", value="acc", title="bar")

    tracklab.log(
        {
            "line1": line_plot,
            "line_series1": line_series_plot,
            "line_series_no_title_no_keys": line_series_plot_no_title_no_keys,
            "line_series_single_x": line_series_singular_x_array,
            "histogram1": histogram,
            "scatter1": scatter,
            "bar1": bar,
        }
    )


if __name__ == "__main__":
    main(sys.argv)
