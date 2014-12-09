import mock
import unittest

from tornado import (
    httpclient,
)

from thuum import runners
from thuum.tests import utils

class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.client = mock.MagicMock()
        self.client.max_clients = 1
        self.client.active = [mock.MagicMock()]
        self.make_request = mock.MagicMock()
        self.events = {
            "ready": mock.MagicMock(),
            "start": mock.MagicMock(),
            "done": mock.MagicMock(),
        }
        self.runner = runners.Runner(self.client, self.make_request)
        self.runner.events.on("request_ready", self.events["ready"])
        self.runner.events.on("request_started", self.events["start"])
        self.runner.events.on("request_done", self.events["done"])

    def test_runner_ready(self):
        self.assertEqual(self.events["ready"].call_count, 0)
        self.assertEqual(self.events["start"].call_count, 0)
        self.assertEqual(self.events["done"].call_count, 0)

    def test_start_request(self):
        self.runner._start_request()

        self.assertEqual(self.events["ready"].call_count, 1)
        self.assertEqual(self.events["start"].call_count, 1)
        self.assertEqual(self.events["done"].call_count, 0)

    def test_finish_request(self):
        self.runner._start_request()
        future = self.runner._pending[0]
        future.set_result(None)

        self.assertEqual(self.events["ready"].call_count, 1)
        self.assertEqual(self.events["start"].call_count, 1)
        self.assertEqual(self.events["done"].call_count, 0)


class QuantityRunnerTests(utils.Base):
    def test_single_request(self):
        make_request = mock.MagicMock(wraps=self.get_request)
        events, runner = self.get_runner(
            runners.QuantityRunner,
            make_request=make_request,
            num_requests=1)

        runner.run()

        self.assertEqual(make_request.call_count, 1)
        self.assertEqual(events["ready"].call_count, 1)
        self.assertEqual(events["start"].call_count, 1)
        self.assertEqual(events["finish"].call_count, 1)

    def test_queued_requests(self):
        self.http_client.max_clients = 1
        make_request = mock.MagicMock(wraps=self.get_request)
        events, runner = self.get_runner(
            runners.QuantityRunner,
            make_request=make_request,
            num_requests=3)

        stop = lambda f: self.http_client.io_loop.stop()
        runner.events.on("request_finished", stop)
        runner.run()

        progress = runner.progress()
        self.assertEqual(progress["total"], 3)
        self.assertGreater(progress["current"], 0)
        self.assertGreater(runner._remaining, 0)
        self.assertGreater(events["ready"].call_count, 0)
        self.assertGreater(events["start"].call_count, 0)
        self.assertEqual(events["finish"].call_count, 1)

    def test_pending_requests_completed(self):
        self.http_client.max_clients = 2
        make_request = mock.MagicMock(wraps=self.get_request)
        events, runner = self.get_runner(
            runners.QuantityRunner,
            make_request=make_request,
            num_requests=2)

        runner.run()

        self.assertEqual(events["start"].call_count, 2)
        self.assertEqual(events["finish"].call_count, 2)


class DurationRunnerTests(utils.Base):
    def test_zero_duration(self):
        make_request = mock.MagicMock(wraps=self.get_request)
        events, runner = self.get_runner(
            runners.DurationRunner,
            make_request=make_request,
            duration=0.001)

        runner.run()
        progress = runner.progress()

        self.assertGreater(events["start"].call_count, 0)
        self.assertGreater(progress["current"], 0)
