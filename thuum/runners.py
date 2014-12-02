import time

from pyee import EventEmitter
from tornado import (
    concurrent,
)

class Runner(object):
    def __init__(self, client, make_request):
        self.client = client
        self.make_request = make_request
        self._pending = []
        self.events = EventEmitter()

    def _on_request_finished(self, _):
        """
        Start the next waiting request if possible.

        """
        if len(self.client.active) < self.client.max_clients:
            self._start_request()

    def _start_request(self):
        """
        Start a request and add callbacks to its future.

        Most notably, the completion of the requests's future will also trigger
        the completion of a future we had prepared earlier.

        """
        request = self.make_request(streaming_callback=lambda c: None)
        future = concurrent.Future()

        self.events.emit("request_ready", future, request)
        self.client.fetch(request, callback=future.set_result)
        self.events.emit("request_started", future)

        self._pending.append(future)
        future.add_done_callback(lambda f: self.events.emit("request_finished", f))
        future.add_done_callback(self._pending.remove)
        future.add_done_callback(self._on_request_finished)


class QuantityRunner(Runner):
    def __init__(self, client, make_request, num_requests):
        super(QuantityRunner, self).__init__(client, make_request)
        self._total = num_requests
        self._remaining = num_requests

    def _on_request_finished(self, _):
        if len(self._pending) == 0 and self._remaining == 0:
            self.client.io_loop.stop()
        elif self._remaining > 0:
            super(QuantityRunner, self)._on_request_finished(_)

    def _start_request(self):
        self._remaining -= 1
        super(QuantityRunner, self)._start_request()

    def run(self):
        self.events.emit("tests_started")
        # Start the number of desired requests, up to the maximum number of
        # desired concurrent requests.
        for _ in xrange(min(self._total, self.client.max_clients)):
            self._start_request()

        # a single future which completes once all futures are complete.
        self.client.io_loop.start()
        self.events.emit("tests_finished")

    def progress(self):
        sent = self._total - self._remaining
        return {
            "unit": "requests",
            "total": self._total,
            "current": sent,
            "percentage": min(100.00, sent / float(self._total) * 100),
        }


class DurationRunner(Runner):
    def __init__(self, client, make_request, duration):
        super(DurationRunner, self).__init__(client, make_request)
        self._duration = duration
        self._started = None

    def run(self):
        self.events.emit("tests_started")
        self._started = time.time()

        # Start the number of desired requests, up to the maximum number of
        # desired concurrent requests.
        for _ in xrange(self.client.max_clients):
            self._start_request()

        self.client.io_loop.call_later(self._duration, self.client.io_loop.stop)
        self.client.io_loop.start()
        self.events.emit("tests_finished")

    def progress(self):
        current = time.time() - self._started
        return {
            "unit": "seconds",
            "total": self._duration,
            "current": current,
            "percentage": min(100.0, current / float(self._duration) * 100),
        }
