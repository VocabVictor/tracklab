# -*- coding: utf-8 -*-
#
# Copyright 2014 Thomas Amland <thomas.amland@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import threading
from collections import deque


class DelayedQueue(object):

    def __init__(self, delay):
        self.delay = delay
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._queue = deque()
        self._closed = False

    def put(self, element):
        """Add element to queue."""
        self._lock.acquire()
        self._queue.append((element, time.time()))
        self._not_empty.notify()
        self._lock.release()

    def close(self):
        """Close queue, indicating no more items will be added."""
        self._closed = True
        self._not_empty.acquire()
        self._not_empty.notify()
        self._not_empty.release()

    def get(self):
        """Remove and return an element from the queue, or this queue has been
        closed raise the Closed exception.
        """
        while True:
            # wait for element to be added to queue
            self._not_empty.acquire()
            while len(self._queue) == 0 and not self._closed:
                self._not_empty.wait()

            if self._closed:
                self._not_empty.release()
                return None
            head, insert_time = self._queue[0]
            self._not_empty.release()

            # wait for delay
            time_left = insert_time + self.delay - time.time()
            while time_left > 0:
                time.sleep(time_left)
                time_left = insert_time + self.delay - time.time()

            self._lock.acquire()
            try:
                if len(self._queue) > 0 and self._queue[0][0] is head:
                    self._queue.popleft()
                    return head
            finally:
                self._lock.release()

    def remove(self, predicate):
        """Remove and return the first items for which predicate is True,
        ignoring delay."""
        try:
            self._lock.acquire()
            for i, (elem, t) in enumerate(self._queue):
                if predicate(elem):
                    del self._queue[i]
                    return elem
        finally:
            self._lock.release()
        return None
