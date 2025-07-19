"""Logging and metrics functionality for Run class."""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import tracklab
from tracklab.sdk import metric
from tracklab.sdk.lib import ipython
from tracklab.util import _is_py_requirements_or_dockerfile

from .run_core import _attach, _log_to_run, _raise_if_finished

if TYPE_CHECKING:
    from tracklab.proto.tracklab_internal_pb2 import MetricRecord
    from tracklab.sdk.run import Run


class LoggingMetrics:
    """Mixin class for logging and metrics functionality."""

    @_log_to_run
    def _metric_callback(self: Run, metric_record: MetricRecord) -> None:
        if self._backend and self._backend.interface:
            self._backend.interface._publish_metric(metric_record)

    def _get_hardware_monitor(self: Run):
        """Get or initialize the hardware monitor."""
        if self._hardware_monitor is None and self._hardware_monitor_enabled:
            try:
                from tracklab.sdk import hardware_monitor
                self._hardware_monitor = hardware_monitor.get_hardware_monitor(self._settings)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to initialize hardware monitor: {e}")
                self._hardware_monitor_enabled = False
        return self._hardware_monitor

    def _enrich_with_hardware_stats(self: Run, data: dict[str, Any]) -> dict[str, Any]:
        """Enrich logging data with hardware statistics."""
        if not self._hardware_monitor_enabled:
            return data
        
        monitor = self._get_hardware_monitor()
        if monitor is None:
            return data
        
        try:
            # Get hardware stats
            hardware_stats = monitor.get_hardware_stats()
            
            # Merge user data with hardware stats
            # User data takes precedence over hardware stats in case of key conflicts
            enriched_data = {**hardware_stats, **data}
            return enriched_data
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to get hardware stats: {e}")
            return data

    def _log(
        self: Run,
        data: dict[str, Any],
        step: int | None = None,
        commit: bool | None = None,
    ) -> None:
        if not isinstance(data, Mapping):
            raise TypeError("tracklab.log must be passed a dictionary")

        if any(not isinstance(key, str) for key in data.keys()):
            raise TypeError("Key values passed to `tracklab.log` must be strings.")

        # Enrich data with hardware monitoring information
        enriched_data = self._enrich_with_hardware_stats(data)

        self._partial_history_callback(enriched_data, step, commit)

        if step is not None:
            if os.getpid() != self._init_pid or self._is_attached:
                tracklab.termwarn(
                    "Note that setting step in multiprocessing can result in data loss. "
                    "You can use multiprocessing in three ways with W&B: "
                    "(1) run multiple `tracklab.init` calls inside an if __name__=='__main__' block, "
                    "(2) call `tracklab.init` once and then pass the run object as an argument to "
                    "the processes, or (3) use `tracklab.init` with `reinit=True`. "
                    "For more details see: https://docs.tracklab.ai/guides/track/launch",
                    repeat=False,
                )

        # TODO: we should have a single callback to handle these cases
        if commit:
            self._enqueue_run(summary=False)
        ipython.maybe_display_html(self.dir)

    @_log_to_run
    @_raise_if_finished
    @_attach
    def log(
        self: Run,
        data: dict[str, Any],
        step: int | None = None,
        commit: bool | None = None,
    ) -> None:
        """Upload run data.

        Use `log` to log data from runs, such as scalars, images, video,
        histograms, plots, and tables. See [Log objects and media](https://docs.tracklab.ai/guides/track/log) for
        code snippets, best practices, and more.

        Basic usage:

        ```python
        import tracklab

        with tracklab.init() as run:
            run.log({"train-loss": 0.5, "accuracy": 0.9})
        ```

        Args:
            data: (dict, optional) A dict of serializable python objects i.e. `str`,
                `ints`, `floats`, `Tensors`, `dicts`, or any of the [W&B data
                types](https://docs.tracklab.ai/guides/track/log).
            commit: (boolean, optional) Save the metrics dict to the tracklab server
                and increment the step.  If false `tracklab.log` just updates the
                current metrics dict with the metrics reported by this call and
                metrics won't be saved until `tracklab.log` is called with
                `commit=True`. Default set to `True`.
            step: (integer, optional) The global step in processing. This persists
                any non-committed earlier steps but does not change the internal
                step counter.

        ```python
        import tracklab

        run = tracklab.init()

        # logs three metrics in a single step with step = 3
        run.log({"a": 10, "b": 0.2}, step=3, commit=False)
        run.log({"c": 0.1}, step=3, commit=False)
        run.log({"d": 100}, step=3, commit=True)
        # logs two metrics in a single step with step = 5
        run.log({"a": 10, "b": 0.2}, step=5, commit=False)
        run.log({"d": 100}, step=5, commit=True)
        ```

        Use `commit=False` to accumulate metrics in memory and reduce write load.

        ### Log data types

        [W&B data types](https://docs.tracklab.ai/guides/track/log#log-a-custom-chart) can be logged with
        `tracklab.log()`. The following example logs a variety of data types and
        creates a dashboard like [this](https://tracklab.ai/stacey/test/reports/Logging-in-W-B--Vmlldzo3NDI0NDA?accessToken=1b05f5e639977f1b961a512a0e75e58befecc75e388d4bc2f3ce9b8294d5f42f):

        ```python
        import tracklab
        import numpy as np

        # Run parameters
        hyperparameters = {
            "learning_rate": 0.02,
            "batch_size": 100,
            "epochs": 10,
        }

        # Define the model architecture - this is a toy example
        model_architecture = {"layer_1": 128, "layer_2": 64, "layer_3": 32}

        # Initialize logging
        tracklab.init(config=hyperparameters, project="test")

        # Simulate one training step
        for epoch in range(hyperparameters["epochs"]):
            loss = epoch / hyperparameters["epochs"]  # Simulate a loss value
            mse = (2 * epoch) / hyperparameters["epochs"]  # Simulate an mse value
            images = np.random.randint(0, 255, (10, 28, 28))

            # Log metrics, images, and custom objects
            tracklab.log(
                {
                    # Scalar values
                    "loss": loss,
                    "mse": mse,
                    # tracklab.Image
                    "image": tracklab.Image(images[0]),
                    # tracklab.Histogram
                    "histogram": tracklab.Histogram(np.random.randn(1000)),
                    # tracklab.Table
                    "table": tracklab.Table(
                        columns=["Layer", "Neurons"],
                        data=[
                            ["Layer 1", model_architecture["layer_1"]],
                            ["Layer 2", model_architecture["layer_2"]],
                            ["Layer 3", model_architecture["layer_3"]],
                        ],
                    ),
                    # Custom object logged as .json
                    "model_architecture": model_architecture,
                    "train_set_size": len(images),
                    # More complex objects
                    "nested_dict": {
                        "a": {
                            "b": {
                                "c": "nested value"
                            }
                        }
                    },
                }
            )

        tracklab.finish()
        ```

        Raises:
            tracklab.Error: if called before `tracklab.init`
            ValueError: if invalid data is passed

        """
        deprecate.deprecate(
            field_name=deprecate.Deprecated.run__log_code_capture_agent,
            warning_message=(
                'tracklab.run.log_code() now has argument "include_fn" that captures files matching "*.py"'
            ),
        )

        if any(_is_py_requirements_or_dockerfile(k) for k in data.keys()):
            tracklab.termwarn(
                "`requirements.txt` found. This file is automatically logged when running `tracklab.init()` with `save_code=True`"
            )

        self._log(data, step, commit)

    @_log_to_run
    @_raise_if_finished
    @_attach
    def define_metric(
        self: Run,
        name: str,
        step_metric: str | metric.Metric | None = None,
        step_sync: bool | None = None,
        hidden: bool | None = None,
        summary: str | None = None,
        goal: str | None = None,
        overwrite: bool | None = None,
    ) -> metric.Metric:
        """Customize metrics logged with `tracklab.log()`.

        Args:
            name: The name of the metric to customize.
            step_metric: The name of another metric to serve as the X-axis
                for this metric in automatically generated charts.
            step_sync: Automatically insert the last value of step_metric into
                `run.log()` if it is not provided explicitly. Defaults to True
                 if step_metric is specified.
            hidden: Hide this metric from automatic plots.
            summary: Specify aggregate metrics added to summary.
                Supported values: "best", "min", "max", "mean", "last", "none".
                Detaults to "last". "best" is deprecated, use "min" or "max" instead.
            goal: Specify how to interpret the metric. Supported values:
                "minimize", "maximize".
            overwrite: If true, overwrite the existing metric with the same name.

        ### Examples:

        You can define a metric to customize how it is displayed, but you cannot
        use `define_metric` to name a metric _created_ in the W&B UI.

        ```python
        import tracklab

        # customize a metric
        tracklab.init()
        tracklab.define_metric("test/accuracy", summary="max", goal="maximize")
        # log the metric with `tracklab.log()`
        tracklab.log({"test/accuracy": 0.9})
        tracklab.finish()
        ```

        Use `step_metric` to set the x-axis using a different metric.

        ```python
        tracklab.init()
        tracklab.define_metric("test/accuracy", step_metric="iterations")
        tracklab.log({"test/accuracy": 0.9, "iterations": 1})
        tracklab.finish()
        ```
        """
        return self._define_metric(
            name,
            step_metric,
            step_sync,
            hidden,
            summary,
            goal,
            overwrite,
        )

    def _define_metric(
        self: Run,
        name: str,
        step_metric: str | metric.Metric | None = None,
        step_sync: bool | None = None,
        hidden: bool | None = None,
        summary: str | None = None,
        goal: str | None = None,
        overwrite: bool | None = None,
    ) -> metric.Metric:
        if not name:
            raise tracklab.Error("define_metric() requires non-empty name argument")
        if isinstance(step_metric, metric.Metric):
            step_metric = step_metric.name
        for arg_name, arg_val, exp_type in (
            ("name", name, str),
            ("step_metric", step_metric, str),
            ("step_sync", step_sync, bool),
            ("hidden", hidden, bool),
            ("summary", summary, str),
            ("goal", goal, str),
            ("overwrite", overwrite, bool),
        ):
            if arg_val is not None and not isinstance(arg_val, exp_type):
                raise TypeError(
                    f'define_metric() expected type "{exp_type.__name__}" '
                    f'for argument "{arg_name}". '
                    f'Received {type(arg_val).__name__} instead.'
                )
        if step_sync is None:
            if step_metric:
                step_sync = True
        defined_metric = metric.Metric(
            name=name,
            step_metric=step_metric,
            step_sync=step_sync,
            hidden=hidden,
            summary=summary,
            goal=goal,
        )
        if overwrite:
            self._metric_mgr.add(defined_metric)
        else:
            self._metric_mgr.define(defined_metric)
        self._enqueue_metric(defined_metric)
        return defined_metric