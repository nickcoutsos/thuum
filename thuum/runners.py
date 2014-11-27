import time

from tornado import (
    concurrent,
)

class Record(object):
    def __init__(self):
        self.start = time.time()
        self.finish = None
        self.code = None
        self.sent = 0
        self.received = 0

    def on_received(self, chunk):
        self.received += len(chunk)

    def complete(self, future):
        response = future.result()
        self.finish = time.time()
        self.code = response.code


class Runner(object):
    def __init__(self, client, make_request):
        self.client = client
        self.make_request = make_request
        self._records = []
        self._pending = []

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
        request = self.make_request()
        future = concurrent.Future()
        record = Record()

        request.streaming_callback = record.on_received
        self.client.fetch(request, callback=future.set_result)

        self._pending.append(future)
        future.add_done_callback(record.complete)
        future.add_done_callback(self._pending.remove)
        future.add_done_callback(lambda f: self._records.append(record))
        future.add_done_callback(self._on_request_finished)


class QuantityRunner(Runner):
    _remaining = None

    def _on_request_finished(self, _):
        if len(self._pending) == 0 and self._remaining == 0:
            self.client.io_loop.stop()
        elif self._remaining > 0:
            super(QuantityRunner, self)._on_request_finished(_)

    def _start_request(self):
        self._remaining -= 1
        super(QuantityRunner, self)._start_request()

    def run(self, num_requests):
        self._remaining = num_requests

        # Start the number of desired requests, up to the maximum number of
        # desired concurrent requests.
        for _ in xrange(min(num_requests, self.client.max_clients)):
            self._start_request()

        # a single future which completes once all futures are complete.
        self.client.io_loop.start()
        return self._records


class DurationRunner(Runner):
    _timeout = None

    def run(self, duration):
        # Start the number of desired requests, up to the maximum number of
        # desired concurrent requests.
        for _ in xrange(self.client.max_clients):
            self._start_request()

        self.client.io_loop.call_later(duration, self.client.io_loop.stop)
        self.client.io_loop.start()
        return self._records
