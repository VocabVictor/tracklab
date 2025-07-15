"""Use tracklab to track machine learning work.

Train and fine-tune models, manage models from experimentation to production.

For guides and examples, see https://docs.tracklab.ai.

For scripts and interactive notebooks, see https://github.com/tracklab/examples.

For reference documentation, see https://docs.tracklab.com/ref/python.
"""
from __future__ import annotations

__version__ = "0.0.2"

# Setup vendor module paths before any other imports
import sys
import os
_vendor_dir = os.path.join(os.path.dirname(__file__), "vendor")
for _vendor_path in ["gql-0.2.0", "graphql-core-1.1", "promise-2.3.0", "watchdog_0_9_0"]:
    _full_path = os.path.join(_vendor_dir, _vendor_path)
    if _full_path not in sys.path:
        sys.path.insert(0, _full_path)


from tracklab.errors import Error

# This needs to be early as other modules call it.
from tracklab.errors.term import termsetup, termlog, termerror, termwarn

# Configure the logger as early as possible for consistent behavior.
from tracklab.sdk.lib import wb_logging as _wb_logging
_wb_logging.configure_wandb_logger()  # TODO: rename function to configure_tracklab_logger

from tracklab import sdk as tracklab_sdk

# Note: tracklab SDK 
tracklab_lib = tracklab_sdk.lib  # type: ignore
# Legacy compatibility for tests that still reference wandb_lib
wandb_lib = tracklab_sdk.lib  # type: ignore

init = tracklab_sdk.init
setup = tracklab_sdk.setup
attach = _attach = tracklab_sdk._attach
_sync = tracklab_sdk._sync
teardown = _teardown = tracklab_sdk.teardown
finish = tracklab_sdk.finish
join = finish
login = tracklab_sdk.login
helper = tracklab_sdk.helper
sweep = tracklab_sdk.sweep
controller = tracklab_sdk.controller
require = tracklab_sdk.require
Artifact = tracklab_sdk.Artifact
AlertLevel = tracklab_sdk.AlertLevel
Settings = tracklab_sdk.Settings
Config = tracklab_sdk.Config

from tracklab.apis import InternalApi, PublicApi
from tracklab.errors import CommError, UsageError

_preinit = tracklab_lib.preinit  # type: ignore
_lazyloader = tracklab_lib.lazyloader  # type: ignore

from tracklab.integration.torch import tracklab_torch

# Move this (keras.__init__ expects it at top level)
from tracklab.sdk.data_types._private import _cleanup_media_tmp_dir

_cleanup_media_tmp_dir()

from tracklab.data_types import Graph
from tracklab.data_types import Image
from tracklab.data_types import Plotly

# from tracklab.data_types import Bokeh # keeping out of top level for now since Bokeh plots have poor UI
from tracklab.data_types import Video
from tracklab.data_types import Audio
from tracklab.data_types import Table
from tracklab.data_types import Html
from tracklab.data_types import box3d
from tracklab.data_types import Object3D
from tracklab.data_types import Molecule
from tracklab.data_types import Histogram
from tracklab.data_types import Classes
from tracklab.data_types import JoinedTable

from tracklab.tracklab_agent import agent

from tracklab.plot import visualize, plot_table
from tracklab.integration.sagemaker import sagemaker_auth
from tracklab.sdk.internal import profiler

# Artifact import types
from tracklab.sdk.artifacts.artifact_ttl import ArtifactTTL

# Used to make sure we don't use some code in the incorrect process context
_IS_INTERNAL_PROCESS = False


def _set_internal_process(disable=False):
    global _IS_INTERNAL_PROCESS
    if _IS_INTERNAL_PROCESS is None:
        return
    if disable:
        _IS_INTERNAL_PROCESS = None
        return
    _IS_INTERNAL_PROCESS = True


def _assert_is_internal_process():
    if _IS_INTERNAL_PROCESS is None:
        return
    assert _IS_INTERNAL_PROCESS


def _assert_is_user_process():
    if _IS_INTERNAL_PROCESS is None:
        return
    assert not _IS_INTERNAL_PROCESS


# globals
Api = PublicApi
api = InternalApi()
run: tracklab_sdk.tracklab_run.Run | None = None
config = _preinit.PreInitObject("tracklab.config", tracklab_sdk.tracklab_config.Config)
summary = _preinit.PreInitObject("tracklab.summary", tracklab_sdk.tracklab_summary.Summary)
log = _preinit.PreInitCallable("tracklab.log", tracklab_sdk.tracklab_run.Run.log)  # type: ignore
watch = _preinit.PreInitCallable("tracklab.watch", tracklab_sdk.tracklab_run.Run.watch)  # type: ignore
unwatch = _preinit.PreInitCallable("tracklab.unwatch", tracklab_sdk.tracklab_run.Run.unwatch)  # type: ignore
save = _preinit.PreInitCallable("tracklab.save", tracklab_sdk.tracklab_run.Run.save)  # type: ignore
restore = tracklab_sdk.tracklab_run.restore
use_artifact = _preinit.PreInitCallable(
    "tracklab.use_artifact", tracklab_sdk.tracklab_run.Run.use_artifact  # type: ignore
)
log_artifact = _preinit.PreInitCallable(
    "tracklab.log_artifact", tracklab_sdk.tracklab_run.Run.log_artifact  # type: ignore
)
log_model = _preinit.PreInitCallable(
    "tracklab.log_model", tracklab_sdk.tracklab_run.Run.log_model  # type: ignore
)
use_model = _preinit.PreInitCallable(
    "tracklab.use_model", tracklab_sdk.tracklab_run.Run.use_model  # type: ignore
)
link_model = _preinit.PreInitCallable(
    "tracklab.link_model", tracklab_sdk.tracklab_run.Run.link_model  # type: ignore
)
define_metric = _preinit.PreInitCallable(
    "tracklab.define_metric", tracklab_sdk.tracklab_run.Run.define_metric  # type: ignore
)

mark_preempting = _preinit.PreInitCallable(
    "tracklab.mark_preempting", tracklab_sdk.tracklab_run.Run.mark_preempting  # type: ignore
)

alert = _preinit.PreInitCallable("tracklab.alert", tracklab_sdk.tracklab_run.Run.alert)  # type: ignore

# record of patched libraries
patched = {"tensorboard": [], "keras": [], "gym": []}  # type: ignore

keras = _lazyloader.LazyLoader("tracklab.keras", globals(), "tracklab.integration.keras")
sklearn = _lazyloader.LazyLoader("tracklab.sklearn", globals(), "tracklab.sklearn")
tensorflow = _lazyloader.LazyLoader(
    "tracklab.tensorflow", globals(), "tracklab.integration.tensorflow"
)
xgboost = _lazyloader.LazyLoader(
    "tracklab.xgboost", globals(), "tracklab.integration.xgboost"
)
catboost = _lazyloader.LazyLoader(
    "tracklab.catboost", globals(), "tracklab.integration.catboost"
)
tensorboard = _lazyloader.LazyLoader(
    "tracklab.tensorboard", globals(), "tracklab.integration.tensorboard"
)
gym = _lazyloader.LazyLoader("tracklab.gym", globals(), "tracklab.integration.gym")
lightgbm = _lazyloader.LazyLoader(
    "tracklab.lightgbm", globals(), "tracklab.integration.lightgbm"
)
jupyter = _lazyloader.LazyLoader("tracklab.jupyter", globals(), "tracklab.jupyter")
sacred = _lazyloader.LazyLoader("tracklab.sacred", globals(), "tracklab.integration.sacred")


def ensure_configured():
    global api
    api = InternalApi()


def set_trace():
    import pdb  # TODO: support other debuggers

    #  frame = sys._getframe().f_back
    pdb.set_trace()  # TODO: pass the parent stack...


def load_ipython_extension(ipython):
    ipython.register_magics(tracklab.jupyter.WandBMagics)


if tracklab_sdk.lib.ipython.in_notebook():
    from IPython import get_ipython  # type: ignore[import-not-found]

    load_ipython_extension(get_ipython())


from .analytics import Sentry as _Sentry

if "dev" in __version__:
    import tracklab.env
    import os

    # Disable error reporting in dev versions.
    os.environ[tracklab.env.ERROR_REPORTING] = os.environ.get(
        tracklab.env.ERROR_REPORTING,
        "false",
    )

_sentry = _Sentry()
_sentry.setup()


__all__ = (
    "__version__",
    "init",
    "finish",
    "setup",
    "save",
    "sweep",
    "controller",
    "agent",
    "config",
    "log",
    "summary",
    "join",
    "Api",
    "Graph",
    "Image",
    "Plotly",
    "Video",
    "Audio",
    "Table",
    "Html",
    "box3d",
    "Object3D",
    "Molecule",
    "Histogram",
    "ArtifactTTL",
    "log_artifact",
    "use_artifact",
    "log_model",
    "use_model",
    "link_model",
    "define_metric",
    "watch",
    "unwatch",
    "plot_table",
)
