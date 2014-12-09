import mock
import unittest

from thuum import runners, stats


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.record = stats.Record()

    def test_complete_record(self):
        future = mock.MagicMock()
        future.result.return_value = mock.MagicMock(code=200)

        self.record.start()
        self.record.complete(future)

        self.assertEqual(future.result.call_count, 1)
        self.assertEqual(self.record.code, 200)

    def test_receive_data(self):
        self.record.on_received("foo")
        self.record.on_received("barbaz")

        self.assertEqual(self.record.received, 9)


class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.tracker = stats.Tracker()

    def test_start_finish(self):
        self.tracker.tests_started()
        self.tracker.tests_finished()

    def test_start_request(self):
        future = mock.MagicMock()
        request = mock.MagicMock()

        self.tracker.request_ready(future, request)

        self.assertIn(future, self.tracker._pending)
        self.assertGreater(len(self.tracker.get_records()), 0)

    def test_finish_request(self):
        future = mock.MagicMock()
        request = mock.MagicMock()

        self.tracker.request_ready(future, request)
        self.tracker.request_started(future)
        self.tracker.request_finished(future)

        self.assertEqual(self.tracker._pending, {})
