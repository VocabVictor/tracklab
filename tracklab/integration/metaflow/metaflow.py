"""W&B Integration for Metaflow.

This integration lets users apply decorators to Metaflow flows and steps to automatically log parameters and artifacts to W&B by type dispatch.

- Decorating a step will enable or disable logging for certain types within that step
- Decorating the flow is equivalent to decorating all steps with a default
- Decorating a step after decorating the flow will overwrite the flow decoration

Examples can be found at wandb/wandb/functional_tests/metaflow
"""

import inspect
import pickle
from functools import wraps
from pathlib import Path
from typing import Union

import tracklab
from tracklab.sdk.lib import telemetry as wb_telemetry

try:
    from metaflow import current
except ImportError as e:
    raise Exception(
        "Error: `metaflow` not installed >> This integration requires metaflow!  To fix, please `pip install -Uqq metaflow`"
    ) from e

try:
    from plum import dispatch
except ImportError as e:
    raise Exception(
        "Error: `plum-dispatch` not installed >> "
        "This integration requires plum-dispatch! To fix, please `pip install -Uqq plum-dispatch`"
    ) from e


try:
    import pandas as pd

    @dispatch
    def _wandb_use(
        name: str,
        data: pd.DataFrame,
        datasets=False,
        run=None,
        testing=False,
        *args,
        **kwargs,
    ):  # type: ignore
        if testing:
            return "datasets" if datasets else None

        if datasets:
            tracklab.termlog(f"Using artifact: {name} ({type(data)})")

    @dispatch
    def wandb_track(
        name: str,
        data: pd.DataFrame,
        datasets=False,
        run=None,
        testing=False,
        *args,
        **kwargs,
    ):
        if testing:
            return "pd.DataFrame" if datasets else None

        if datasets:
            with artifact.new_file(f"{name}.parquet", "wb") as f:
                data.to_parquet(f, engine="pyarrow")
            tracklab.termlog(f"Logging artifact: {name} ({type(data)})")

except ImportError:
    tracklab.termwarn(
        "`pandas` not installed >> @wandb_log(datasets=True) may not auto log your dataset!"
    )

try:
    import torch
    import torch.nn as nn

    @dispatch
    def _wandb_use(
        name: str,
        data: nn.Module,
        models=False,
        run=None,
        testing=False,
        *args,
        **kwargs,
    ):  # type: ignore
        if testing:
            return "models" if models else None

        if models:
            tracklab.termlog(f"Using artifact: {name} ({type(data)})")

    @dispatch
    def wandb_track(
        name: str,
        data: nn.Module,
        models=False,
        run=None,
        testing=False,
        *args,
        **kwargs,
    ):
        if testing:
            return "nn.Module" if models else None

        if models:
            with artifact.new_file(f"{name}.pkl", "wb") as f:
                torch.save(data, f)
            tracklab.termlog(f"Logging artifact: {name} ({type(data)})")

except ImportError:
    tracklab.termwarn(
        "`pytorch` not installed >> @wandb_log(models=True) may not auto log your model!"
    )

try:
    from sklearn.base import BaseEstimator

    @dispatch
    def _wandb_use(
        name: str,
        data: BaseEstimator,
        models=False,
        run=None,
        testing=False,
        *args,
        **kwargs,
    ):  # type: ignore
        if testing:
            return "models" if models else None

        if models:
            tracklab.termlog(f"Using artifact: {name} ({type(data)})")

    @dispatch
    def wandb_track(
        name: str,
        data: BaseEstimator,
        models=False,
        run=None,
        testing=False,
        *args,
        **kwargs,
    ):
        if testing:
            return "BaseEstimator" if models else None

        if models:
            with artifact.new_file(f"{name}.pkl", "wb") as f:
                pickle.dump(data, f)
            tracklab.termlog(f"Logging artifact: {name} ({type(data)})")

except ImportError:
    tracklab.termwarn(
        "`sklearn` not installed >> @wandb_log(models=True) may not auto log your model!"
    )


class ArtifactProxy:
    def __init__(self, flow):
        # do this to avoid recursion problem with __setattr__
        self.__dict__.update(
            {
                "flow": flow,
                "inputs": {},
                "outputs": {},
                "base": set(dir(flow)),
                "params": {p: getattr(flow, p) for p in current.parameter_names},
            }
        )

    def __setattr__(self, key, val):
        self.outputs[key] = val
        return setattr(self.flow, key, val)

    def __getattr__(self, key):
        if key not in self.base and key not in self.outputs:
            self.inputs[key] = getattr(self.flow, key)
        return getattr(self.flow, key)


@dispatch
def wandb_track(
    name: str,
    data: Union[dict, list, set, str, int, float, bool],
    run=None,
    testing=False,
    *args,
    **kwargs,
):  # type: ignore
    if testing:
        return "scalar"

    run.log({name: data})


@dispatch
def wandb_track(
    name: str, data: Path, datasets=False, run=None, testing=False, *args, **kwargs
):
    if testing:
        return "Path" if datasets else None

    if datasets:
        if data.is_dir():
            artifact.add_dir(data)
        elif data.is_file():
            artifact.add_file(data)
        tracklab.termlog(f"Logging artifact: {name} ({type(data)})")


# this is the base case
@dispatch
def wandb_track(
    name: str, data, others=False, run=None, testing=False, *args, **kwargs
):
    if testing:
        return "generic" if others else None

    if others:
        with artifact.new_file(f"{name}.pkl", "wb") as f:
            pickle.dump(data, f)
        tracklab.termlog(f"Logging artifact: {name} ({type(data)})")


@dispatch
def wandb_use(name: str, data, *args, **kwargs):
    try:
        return _wandb_use(name, data, *args, **kwargs)
    except tracklab.CommError:
        tracklab.termwarn(
            f"This artifact ({name}, {type(data)}) does not exist in the wandb datastore!"
            f"If you created an instance inline (e.g. sklearn.ensemble.RandomForestClassifier), then you can safely ignore this"
            f"Otherwise you may want to check your internet connection!"
        )


@dispatch
def wandb_use(
    name: str, data: Union[dict, list, set, str, int, float, bool], *args, **kwargs
):  # type: ignore
    pass  # do nothing for these types


@dispatch
def _wandb_use(
    name: str, data: Path, datasets=False, run=None, testing=False, *args, **kwargs
):  # type: ignore
    if testing:
        return "datasets" if datasets else None

    if datasets:
        tracklab.termlog(f"Using artifact: {name} ({type(data)})")


@dispatch
def _wandb_use(name: str, data, others=False, run=None, testing=False, *args, **kwargs):  # type: ignore
    if testing:
        return "others" if others else None

    if others:
        tracklab.termlog(f"Using artifact: {name} ({type(data)})")


def coalesce(*arg):
    return next((a for a in arg if a is not None), None)


def wandb_log(
    func=None,
    # /,  # py38 only
    datasets=False,
    models=False,
    others=False,
    settings=None,
):
    """Automatically log parameters and artifacts to W&B by type dispatch.

    This decorator can be applied to a flow, step, or both.
    - Decorating a step will enable or disable logging for certain types within that step
    - Decorating the flow is equivalent to decorating all steps with a default
    - Decorating a step after decorating the flow will overwrite the flow decoration

    Args:
        func: (`Callable`). The method or class being decorated (if decorating a step or flow respectively).
        datasets: (`bool`). If `True`, log datasets.  Datasets can be a `pd.DataFrame` or `pathlib.Path`.  The default value is `False`, so datasets are not logged.
        models: (`bool`). If `True`, log models.  Models can be a `nn.Module` or `sklearn.base.BaseEstimator`.  The default value is `False`, so models are not logged.
        others: (`bool`). If `True`, log anything pickle-able.  The default value is `False`, so files are not logged.
        settings: (`tracklab.sdk.settings.Settings`). Custom settings passed to `tracklab.init`.  The default value is `None`, and is the same as passing `tracklab.Settings()`.  If `settings.run_group` is `None`, it will be set to `{flow_name}/{run_id}.  If `settings.run_job_type` is `None`, it will be set to `{run_job_type}/{step_name}`
    """

    @wraps(func)
    def decorator(func):
        # If you decorate a class, apply the decoration to all methods in that class
        if inspect.isclass(func):
            cls = func
            for attr in cls.__dict__:
                if callable(getattr(cls, attr)):
                    if not hasattr(attr, "_base_func"):
                        setattr(cls, attr, decorator(getattr(cls, attr)))
            return cls

        # prefer the earliest decoration (i.e. method decoration overrides class decoration)
        if hasattr(func, "_base_func"):
            return func

        @wraps(func)
        def wrapper(self, *args, settings=settings, **kwargs):
            if not isinstance(settings, tracklab.sdk.settings.Settings):
                settings = tracklab.Settings()

            settings.update_from_dict(
                {
                    "run_group": coalesce(
                        settings.run_group, f"{current.flow_name}/{current.run_id}"
                    ),
                    "run_job_type": coalesce(settings.run_job_type, current.step_name),
                }
            )

            with tracklab.init(settings=settings) as run:
                with wb_telemetry.context(run=run) as tel:
                    tel.feature.metaflow = True
                proxy = ArtifactProxy(self)
                run.config.update(proxy.params)
                func(proxy, *args, **kwargs)

                for name, data in proxy.inputs.items():
                    wandb_use(
                        name,
                        data,
                        datasets=datasets,
                        models=models,
                        others=others,
                        run=run,
                    )

                for name, data in proxy.outputs.items():
                    wandb_track(
                        name,
                        data,
                        datasets=datasets,
                        models=models,
                        others=others,
                        run=run,
                    )

        wrapper._base_func = func

        # Add for testing visibility
        wrapper._kwargs = {
            "datasets": datasets,
            "models": models,
            "others": others,
            "settings": settings,
        }
        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)
