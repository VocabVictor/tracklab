"""monkeypatch: patch code to add tensorboard hooks."""

import os
import re
import socket
from typing import Any, Optional

import tracklab
import tracklab.util

TENSORBOARD_C_MODULE = "tensorflow.python.ops.gen_summary_ops"
TENSORBOARD_X_MODULE = "tensorboardX.writer"
TENSORFLOW_PY_MODULE = "tensorflow.python.summary.writer.writer"
TENSORBOARD_WRITER_MODULE = "tensorboard.summary.writer.event_file_writer"
TENSORBOARD_PYTORCH_MODULE = "torch.utils.tensorboard.writer"


def unpatch() -> None:
    for module, method in tracklab.patched["tensorboard"]:
        writer = tracklab.util.get_module(module, lazy=False)
        setattr(writer, method, getattr(writer, f"orig_{method}"))
    tracklab.patched["tensorboard"] = []


def patch(
    save: bool = True,
    tensorboard_x: Optional[bool] = None,
    pytorch: Optional[bool] = None,
    root_logdir: str = "",
) -> None:
    if len(tracklab.patched["tensorboard"]) > 0:
        raise ValueError(
            "Tensorboard already patched. Call `tracklab.tensorboard.unpatch()` first; "
            "remove `sync_tensorboard=True` from `tracklab.init`; "
            "or only call `tracklab.tensorboard.patch` once."
        )

    # TODO: Some older versions of tensorflow don't require tensorboard to be present.
    # we may want to lift this requirement, but it's safer to have it for now
    tracklab.util.get_module(
        "tensorboard", required="Please install tensorboard package", lazy=False
    )
    c_writer = tracklab.util.get_module(TENSORBOARD_C_MODULE, lazy=False)
    py_writer = tracklab.util.get_module(TENSORFLOW_PY_MODULE, lazy=False)
    tb_writer = tracklab.util.get_module(TENSORBOARD_WRITER_MODULE, lazy=False)
    pt_writer = tracklab.util.get_module(TENSORBOARD_PYTORCH_MODULE, lazy=False)
    tbx_writer = tracklab.util.get_module(TENSORBOARD_X_MODULE, lazy=False)

    if not pytorch and not tensorboard_x and c_writer:
        _patch_tensorflow2(
            writer=c_writer,
            module=TENSORBOARD_C_MODULE,
            save=save,
            root_logdir=root_logdir,
        )
    if py_writer:
        _patch_file_writer(
            writer=py_writer,
            module=TENSORFLOW_PY_MODULE,
            save=save,
            root_logdir=root_logdir,
        )
    if tb_writer:
        _patch_file_writer(
            writer=tb_writer,
            module=TENSORBOARD_WRITER_MODULE,
            save=save,
            root_logdir=root_logdir,
        )
    if pt_writer:
        _patch_file_writer(
            writer=pt_writer,
            module=TENSORBOARD_PYTORCH_MODULE,
            save=save,
            root_logdir=root_logdir,
        )
    if tbx_writer:
        _patch_file_writer(
            writer=tbx_writer,
            module=TENSORBOARD_X_MODULE,
            save=save,
            root_logdir=root_logdir,
        )
    if not c_writer and not tb_writer and not tb_writer:
        tracklab.termerror("Unsupported tensorboard configuration")


def _patch_tensorflow2(
    writer: Any,
    module: Any,
    save: bool = True,
    root_logdir: str = "",
) -> None:
    # This configures TensorFlow 2 style Tensorboard logging
    old_csfw_func = writer.create_summary_file_writer
    logdir_hist = []

    def new_csfw_func(*args: Any, **kwargs: Any) -> Any:
        logdir = (
            kwargs["logdir"].numpy().decode("utf8")
            if hasattr(kwargs["logdir"], "numpy")
            else kwargs["logdir"]
        )
        logdir_hist.append(logdir)
        root_logdir_arg = root_logdir

        if len(set(logdir_hist)) > 1 and root_logdir == "":
            tracklab.termwarn(
                "When using several event log directories, "
                'please call `tracklab.tensorboard.patch(root_logdir="...")` before `tracklab.init`'
            )
        # In this case, the generated logdir
        # is generated and ends with the hostname, update the root_logdir to match.
        hostname = socket.gethostname()
        search = re.search(rf"-\d+_{hostname}", logdir)
        if search:
            root_logdir_arg = logdir[: search.span()[1]]
        elif root_logdir is not None and not os.path.abspath(logdir).startswith(
            os.path.abspath(root_logdir)
        ):
            tracklab.termwarn(
                "Found log directory outside of given root_logdir, "
                f"dropping given root_logdir for event file in {logdir}"
            )
            root_logdir_arg = ""

        _notify_tensorboard_logdir(logdir, save=save, root_logdir=root_logdir_arg)
        return old_csfw_func(*args, **kwargs)

    writer.orig_create_summary_file_writer = old_csfw_func
    writer.create_summary_file_writer = new_csfw_func
    tracklab.patched["tensorboard"].append([module, "create_summary_file_writer"])


def _patch_file_writer(
    writer: Any,
    module: Any,
    save: bool = True,
    root_logdir: str = "",
) -> None:
    logdir_hist = []

    class TBXEventFileWriter(writer.EventFileWriter):
        def __init__(self, logdir: str, *args: Any, **kwargs: Any) -> None:
            logdir_hist.append(logdir)
            root_logdir_arg = root_logdir
            if len(set(logdir_hist)) > 1 and root_logdir == "":
                tracklab.termwarn(
                    "When using several event log directories, "
                    'please call `tracklab.tensorboard.patch(root_logdir="...")` before `tracklab.init`'
                )

            # In this case, the logdir is generated and ends with the hostname,
            # update the root_logdir to match.
            hostname = socket.gethostname()
            search = re.search(rf"-\d+_{hostname}", logdir)
            if search:
                root_logdir_arg = logdir[: search.span()[1]]

            elif root_logdir is not None and not os.path.abspath(logdir).startswith(
                os.path.abspath(root_logdir)
            ):
                tracklab.termwarn(
                    "Found log directory outside of given root_logdir, "
                    f"dropping given root_logdir for event file in {logdir}"
                )
                root_logdir_arg = ""

            _notify_tensorboard_logdir(logdir, save=save, root_logdir=root_logdir_arg)

            super().__init__(logdir, *args, **kwargs)

    writer.orig_EventFileWriter = writer.EventFileWriter
    writer.EventFileWriter = TBXEventFileWriter
    tracklab.patched["tensorboard"].append([module, "EventFileWriter"])


def _notify_tensorboard_logdir(
    logdir: str, save: bool = True, root_logdir: str = ""
) -> None:
    if tracklab.run is not None:
        tracklab.run._tensorboard_callback(logdir, save=save, root_logdir=root_logdir)
