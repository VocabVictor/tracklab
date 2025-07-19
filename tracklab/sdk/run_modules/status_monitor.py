"""Status monitoring functionality for Run class."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import TYPE_CHECKING, Any, Callable, NamedTuple

import tracklab
from tracklab.sdk.lib import wb_logging
from tracklab.sdk.lib import interrupt
from tracklab.sdk.mailbox import HandleAbandonedError, MailboxClosedError, MailboxHandle

if TYPE_CHECKING:
    from tracklab.proto.tracklab_internal_pb2 import Result
    from tracklab.sdk.interface.interface import InterfaceBase
    from tracklab.sdk.settings import Settings


class TeardownStage(IntEnum):
    EARLY = 1
    LATE = 2


class TeardownHook(NamedTuple):
    call: Callable[[], None]
    stage: TeardownStage


@dataclass
class RunStatus:
    sync_items_total: int = field(default=0)
    sync_items_pending: int = field(default=0)
    sync_time: datetime | None = field(default=None)


class RunStatusChecker:
    """Periodically polls the background process for relevant updates.

    - check if the user has requested a stop.
    - check the network status.
    - check the run sync status.
    """

    _stop_status_lock: threading.Lock
    _stop_status_handle: MailboxHandle[Result] | None
    _network_status_lock: threading.Lock
    _network_status_handle: MailboxHandle[Result] | None
    _internal_messages_lock: threading.Lock
    _internal_messages_handle: MailboxHandle[Result] | None

    def __init__(
        self,
        run_id: str,
        interface: InterfaceBase,
        settings: Settings,
        stop_polling_interval: int = 15,
        retry_polling_interval: int = 5,
        internal_messages_polling_interval: int = 10,
    ) -> None:
        self._run_id = run_id
        self._interface = interface
        self._stop_polling_interval = stop_polling_interval
        self._retry_polling_interval = retry_polling_interval
        self._internal_messages_polling_interval = internal_messages_polling_interval
        self._settings = settings

        self._join_event = threading.Event()

        self._stop_status_lock = threading.Lock()
        self._stop_status_handle = None
        self._stop_thread = threading.Thread(
            target=self.check_stop_status,
            name="ChkStopThr",
            daemon=True,
        )

        self._network_status_lock = threading.Lock()
        self._network_status_handle = None
        self._network_status_thread = threading.Thread(
            target=self.check_network_status,
            name="NetStatThr",
            daemon=True,
        )

        self._internal_messages_lock = threading.Lock()
        self._internal_messages_handle = None
        self._internal_messages_thread = threading.Thread(
            target=self.check_internal_messages,
            name="IntMsgThr",
            daemon=True,
        )

    def start(self) -> None:
        self._stop_thread.start()
        self._network_status_thread.start()
        self._internal_messages_thread.start()

    @staticmethod
    def _abandon_status_check(
        lock: threading.Lock,
        handle: MailboxHandle[Result] | None,
    ):
        with lock:
            if handle:
                handle.abandon()

    def _loop_check_status(
        self,
        *,
        lock: threading.Lock,
        set_handle: Any,
        timeout: int,
        request: Any,
        process: Any,
    ) -> None:
        local_handle: MailboxHandle[Result] | None = None
        join_requested = False
        while not join_requested:
            time_probe = time.monotonic()
            if not local_handle:
                try:
                    local_handle = request()
                except MailboxClosedError:
                    # This can happen if the service process dies.
                    break
            assert local_handle

            with lock:
                if self._join_event.is_set():
                    break
                set_handle(local_handle)

            try:
                result = local_handle.wait_or(timeout=timeout)
            except HandleAbandonedError:
                # This can happen if the service process dies.
                break
            except TimeoutError:
                result = None

            with lock:
                set_handle(None)

            if result:
                process(result)
                local_handle = None

            time_elapsed = time.monotonic() - time_probe
            wait_time = max(timeout - time_elapsed, 0)
            join_requested = self._join_event.wait(timeout=wait_time)

    def check_network_status(self) -> None:
        def _process_network_status(result: Result) -> None:
            network_status = result.response.network_status_response
            for hr in network_status.network_responses:
                if (
                    hr.http_status_code == 200 or hr.http_status_code == 0
                ):  # we use 0 for non-http errors (eg wandb errors)
                    tracklab.termlog(f"{hr.http_response_text}")
                else:
                    tracklab.termlog(
                        f"{hr.http_status_code} encountered ({hr.http_response_text.rstrip()}), retrying request"
                    )

        with wb_logging.log_to_run(self._run_id):
            try:
                self._loop_check_status(
                    lock=self._network_status_lock,
                    set_handle=lambda x: setattr(self, "_network_status_handle", x),
                    timeout=self._retry_polling_interval,
                    request=self._interface.deliver_network_status,
                    process=_process_network_status,
                )
            except BrokenPipeError:
                self._abandon_status_check(
                    self._network_status_lock,
                    self._network_status_handle,
                )

    def check_stop_status(self) -> None:
        def _process_stop_status(result: Result) -> None:
            stop_status = result.response.stop_status_response
            if stop_status.run_should_stop:
                # until WB-3606 is resolved on server side.
                if not tracklab.agents.pyagent.is_running():  # type: ignore
                    interrupt.interrupt_main()
                    return

        with wb_logging.log_to_run(self._run_id):
            try:
                self._loop_check_status(
                    lock=self._stop_status_lock,
                    set_handle=lambda x: setattr(self, "_stop_status_handle", x),
                    timeout=self._stop_polling_interval,
                    request=self._interface.deliver_stop_status,
                    process=_process_stop_status,
                )
            except BrokenPipeError:
                self._abandon_status_check(
                    self._stop_status_lock,
                    self._stop_status_handle,
                )

    def check_internal_messages(self) -> None:
        def _process_internal_messages(result: Result) -> None:
            if (
                not self._settings.show_warnings
                or self._settings.quiet
                or self._settings.silent
            ):
                return
            internal_messages = result.response.internal_messages_response
            for msg in internal_messages.messages.warning:
                tracklab.termwarn(msg, repeat=False)

        with wb_logging.log_to_run(self._run_id):
            try:
                self._loop_check_status(
                    lock=self._internal_messages_lock,
                    set_handle=lambda x: setattr(self, "_internal_messages_handle", x),
                    timeout=self._internal_messages_polling_interval,
                    request=self._interface.deliver_internal_messages,
                    process=_process_internal_messages,
                )
            except BrokenPipeError:
                self._abandon_status_check(
                    self._internal_messages_lock,
                    self._internal_messages_handle,
                )

    def stop(self) -> None:
        self._join_event.set()
        self._abandon_status_check(
            self._stop_status_lock,
            self._stop_status_handle,
        )
        self._abandon_status_check(
            self._network_status_lock,
            self._network_status_handle,
        )
        self._abandon_status_check(
            self._internal_messages_lock,
            self._internal_messages_handle,
        )

    def join(self) -> None:
        self.stop()
        self._stop_thread.join()
        self._network_status_thread.join()
        self._internal_messages_thread.join()