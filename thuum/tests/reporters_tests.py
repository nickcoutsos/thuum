import StringIO
import unittest

import mock

from thuum import reporters


class TerimalReporterTests(unittest.TestCase):
    OUTPUT_LINES_PATTERN = "\n".join([
        r"Requests\s*\d+",
        r"Duration\s*\d+\.\d+s",
        r"Average\s*\d+\.\d+s",
        r"Fastest\s*\d+\.\d+s",
        r"Slowest\s*\d+\.\d+s",
        r"Deviation\s*\d+\.\d+",
        r"Received\s*\d+B",
        r"RPS\s*\d+\.\d+",
    ])

    def setUp(self):
        self.stream = StringIO.StringIO()

    def test_progress_no_tty(self):
        runner = mock.MagicMock()
        runner.progress.return_value = {"foo": "bar"}
        reporter = reporters.TerminalReporter(self.stream)

        reporter.progress(runner)

        self.assertEqual(self.stream.getvalue(), "")

    def test_progress_fake_tty(self):
        self.stream.isatty = mock.MagicMock(return_value=True)
        reporter = reporters.TerminalReporter(self.stream)
        runner = mock.MagicMock()
        runner.progress.return_value = {
            "current": 10,
            "total": 20,
            "unit": "foo",
            "percentage": 50.0
        }

        reporter.progress(runner)

        self.assertEqual(self.stream.getvalue(), "\r[10.0/20.0 foo] 50.0%")

    def test_report_summarize(self):
        reporter = reporters.TerminalReporter(self.stream)
        tracker = mock.MagicMock()
        tracker.get_records.return_value = [
            mock.MagicMock(started=0, finished=100, code=200, received=0),
            mock.MagicMock(started=0, finished=100, code=200, received=0),
            mock.MagicMock(started=0, finished=100, code=200, received=0),
        ]

        reporter.summarize(tracker)

        self.assertRegexpMatches(
            self.stream.getvalue(),
            self.OUTPUT_LINES_PATTERN)

    def test_report_summarize_none_finished(self):
        reporter = reporters.TerminalReporter(self.stream)
        tracker = mock.MagicMock()
        tracker.get_records.return_value = [
            mock.MagicMock(started=0, finished=None),
            mock.MagicMock(started=0, finished=None),
            mock.MagicMock(started=0, finished=None),
        ]

        reporter.summarize(tracker)

        self.assertEqual(self.stream.getvalue(), "\n**No completed requests**")


class CSVReporterTests(unittest.TestCase):
    def setUp(self):
        self.stream = StringIO.StringIO()

    def test_report(self):
        reporter = reporters.CSVReporter(self.stream)
        record = mock.Mock(started=0, finished=100, code=200, sent=0, received=0)

        reporter.record(record)

        self.assertEqual(self.stream.getvalue().strip(), "0,100,200,0,0")


class JSONReporterTests(unittest.TestCase):
    def setUp(self):
        self.stream = StringIO.StringIO()

    def test_report(self):
        reporter = reporters.JSONReporter(self.stream)
        record = mock.Mock(started=0, finished=100, code=200, sent=0, received=0)

        reporter.record(record)

        self.assertEqual(
            self.stream.getvalue().strip(),
            """{"code": 200, "finished": 100, "received": 0, "sent": 0, "started": 0}""")
