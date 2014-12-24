import mock
import StringIO
import unittest

from thuum import stats


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

    def test_attach_tracker(self):
        runner = mock.MagicMock()

        tracker = stats.Tracker(runner)

        calls = [args for args, _ in runner.events.on.call_args_list]
        self.assertIn(("tests_started", tracker.tests_started), calls)
        self.assertIn(("tests_finished", tracker.tests_finished), calls)
        self.assertIn(("request_ready", tracker.request_ready), calls)
        self.assertIn(("request_started", tracker.request_started), calls)
        self.assertIn(("request_finished", tracker.request_finished), calls)


class Function_get_time_stats_Tests(unittest.TestCase):
    def setUp(self):
        self.records = [
            mock.MagicMock(started=0, finished=100, code=200, sent=20, received=200),
            mock.MagicMock(started=1, finished=80, code=200, sent=20, received=200),
            mock.MagicMock(started=2, finished=120, code=404, sent=20, received=40),
            mock.MagicMock(started=3, finished=200, code=200, sent=20, received=200),
        ]

    def test_get_time_stats(self):
        records = self.records

        results = stats.get_time_stats(records)

        self.assertEqual(results["count"], 4)
        self.assertEqual(results["dur"], 200)
        self.assertEqual(results["avg"], (100 + 79 + 118 + 197) / 4.0)
        self.assertEqual(results["min"], 79)
        self.assertEqual(results["max"], 197)
        self.assertEqual(results["rps"], 0.02)
        self.assertEqual(results["received"], 640)

    def test_get_time_stats_for_no_results(self):
        records = []

        results = stats.get_time_stats(records)

        self.assertIsNone(results)

    def test_get_time_stats_for_incomplete_results(self):
        records = [
            mock.MagicMock(
                started=0,
                finished=None,
                code=None,
                sent=20,
                received=None)
        ]

        results = stats.get_time_stats(records)

        self.assertIsNone(results)


class Function_print_results_Tests(unittest.TestCase):
    def setUp(self):
        self.stream = StringIO.StringIO()
        self.stats = {
            "count": 4,
            "dur": 200,
            "avg": 20,
            "min": 2,
            "max": 40,
            "rps": 0.02,
            "received": 640,
            "dev": 12
        }

    @mock.patch("thuum.stats.get_time_stats")
    def test_print_stats(self, get_time_stats):
        get_time_stats.return_value = self.stats
        stats.print_results([], stream=self.stream)

        expected = """\
Requests             4
Duration           200.0000s
Average             20.0000s
Fastest              2.0000s
Slowest             40.0000s
Deviation           12.0000
Received           640B
RPS                  0.02
"""

        self.assertEqual(self.stream.getvalue(), expected)


class Function_print_errors_Tests(unittest.TestCase):
    def setUp(self):
        self.records = [
            mock.MagicMock(started=0, finished=100, code=200, sent=20, received=200),
            mock.MagicMock(started=1, finished=80, code=200, sent=20, received=200),
            mock.MagicMock(started=2, finished=120, code=404, sent=20, received=40),
            mock.MagicMock(started=3, finished=200, code=200, sent=20, received=200),
        ]
        self.stream = StringIO.StringIO()

    def test_print_errors(self):
        stats.print_errors(self.records, self.stream)

        self.assertEqual(self.stream.getvalue(), "404 errors: 1\n")
