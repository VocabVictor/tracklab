"""Core decorators and utilities for Run class."""

from __future__ import annotations

import functools
import os
from typing import TYPE_CHECKING, Callable, TypeVar

from typing_extensions import Concatenate, ParamSpec

import tracklab
from tracklab.errors import UsageError
from tracklab.sdk.lib import wb_logging

if TYPE_CHECKING:
    from tracklab.sdk.run import Run

_P = ParamSpec("_P")
_T = TypeVar("_T")


def _log_to_run(
    func: Callable[Concatenate[Run, _P], _T],
) -> Callable[Concatenate[Run, _P], _T]:
    """Decorate a Run method to set the run ID in the logging context.

    Any logs during the execution of the method go to the run's log file
    and not to other runs' log files.

    This is meant for use on all public methods and some callbacks. Private
    methods can be assumed to be called from some public method somewhere.
    The general rule is to use it on methods that can be called from a
    context that isn't specific to this run (such as all user code or
    internal methods that aren't run-specific).
    """

    @functools.wraps(func)
    def wrapper(self: Run, *args, **kwargs) -> _T:
        # In "attach" usage, many properties of the Run are not initially
        # populated.
        if hasattr(self, "_settings"):
            run_id = self._settings.run_id
        else:
            run_id = self._attach_id

        with wb_logging.log_to_run(run_id):
            return func(self, *args, **kwargs)

    return wrapper


_is_attaching: str = ""


def _attach(
    func: Callable[Concatenate[Run, _P], _T],
) -> Callable[Concatenate[Run, _P], _T]:
    """Decorate a Run method to auto-attach when in a new process.

    When in a forked process or using a pickled Run instance, this automatically
    connects to the service process to "attach" to the existing run.
    """

    @functools.wraps(func)
    def wrapper(self: Run, *args, **kwargs) -> _T:
        global _is_attaching

        # The _attach_id attribute is only None when running in the "disable
        # service" mode.
        #
        # Since it is set early in `__init__` and included in the run's pickled
        # state, the attribute always exists.
        is_using_service = self._attach_id is not None

        # The _attach_pid attribute is not pickled, so it might not exist.
        # It is set when the run is initialized.
        attach_pid = getattr(self, "_attach_pid", None)

        if is_using_service and attach_pid != os.getpid():
            if _is_attaching:
                raise RuntimeError(
                    f"Trying to attach `{func.__name__}`"
                    f" while in the middle of attaching `{_is_attaching}`"
                )

            _is_attaching = func.__name__
            try:
                tracklab._attach(run=self)  # type: ignore
            finally:
                _is_attaching = ""

        return func(self, *args, **kwargs)

    return wrapper


def _raise_if_finished(
    func: Callable[Concatenate[Run, _P], _T],
) -> Callable[Concatenate[Run, _P], _T]:
    """Decorate a Run method to raise an error after the run is finished."""

    @functools.wraps(func)
    def wrapper_fn(self: Run, *args, **kwargs) -> _T:
        if not getattr(self, "_is_finished", False):
            return func(self, *args, **kwargs)

        message = (
            f"Run ({self.id}) is finished. The call to"
            f" `{func.__name__}` will be ignored."
            f" Please make sure that you are using an active run."
        )

        raise UsageError(message)

    return wrapper_fn