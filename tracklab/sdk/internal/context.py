"""Context Keeper."""

import logging
import threading
from typing import Dict, Optional

from tracklab.proto.tracklab_internal_pb2 import Record, Result

logger = logging.getLogger(__name__)


class Context:
    _cancel_event: threading.Event
    # _debug_record: Optional[Record]

    def __init__(self) -> None:
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    @property
    def cancel_event(self) -> threading.Event:
        return self._cancel_event


def context_id_from_record(record: Record) -> str:
    context_id = record.control.mailbox_slot
    return context_id


def context_id_from_result(result: Result) -> str:
    context_id = result.control.mailbox_slot
    return context_id


class ContextKeeper:
    _active_items: Dict[str, Context]

    def __init__(self) -> None:
        self._active_items = {}

    def add_from_record(self, record: Record) -> Optional[Context]:
        context_id = context_id_from_record(record)
        if not context_id:
            return None
        context_obj = self.add(context_id)


        return context_obj

    def add(self, context_id: str) -> Context:
        assert context_id
        context_obj = Context()
        self._active_items[context_id] = context_obj
        return context_obj

    def get(self, context_id: str) -> Optional[Context]:
        item = self._active_items.get(context_id)
        return item

    def release(self, context_id: str) -> None:
        if not context_id:
            return
        _ = self._active_items.pop(context_id, None)

    def cancel(self, context_id: str) -> bool:
        item = self.get(context_id)
        if item:
            item.cancel()
            return True
        return False

    #         )
