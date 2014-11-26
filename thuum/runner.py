import time

from tornado import (
    concurrent,
)

from thuum.util import combine_futures

class Runner(object):
    def __init__(self, client, make_request):
        self.client = client
        self.make_request = make_request
        self._waiting = None

    def run(self, num_requests):
        futures = [concurrent.Future() for _ in xrange(num_requests)]
        self._waiting = futures[:]

        # Start the number of desired requests, up to the maximum number of
        # desired concurrent requests.
        for _ in xrange(min(num_requests, self.client.max_clients)):
            self._start_request()

        # a single future which completes once all futures are complete.
        all_done = combine_futures(*futures)
        all_done.add_done_callback(lambda f: self.client.io_loop.stop())
        self.client.io_loop.start()

        return [f.result() for f in futures]

    def _on_request_finished(self, _):
        """
        Start the next waiting request if possible.

        """
        if len(self._waiting) == 0:
            return
        if len(self.client.active) < self.client.max_clients:
            self._start_request()

    def _start_request(self):
        """
        Start a request and add callbacks to its future.

        Most notably, the completion of the requests's future will also trigger
        the completion of a future we had prepared earlier.

        """
        request_future = self._waiting.pop(0)
        response_future = concurrent.Future()
        self.client.fetch(
            self.make_request(),
            callback=response_future.set_result)

        response_future.add_done_callback(self._on_request_finished)
        concurrent.chain_future(response_future, request_future)
