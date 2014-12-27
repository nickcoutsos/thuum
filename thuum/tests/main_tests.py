import mock
import StringIO
import unittest

from thuum import (
    __main__ as main_,
    reporters,
    runners,
)

class ExitException(Exception):
    pass

def mock_runner(*_):
    runner = mock.MagicMock()
    runner.progress.return_value = {
        "current": 1,
        "total": 2,
        "unit": "requests",
        "percentage": 50.00
    }
    return runner

def mock_tracker(*_):
    tracker = mock.MagicMock()
    tracker.get_records.return_value = [
        mock.MagicMock(started=0, finished=100, code=200, sent=0, received=100),
        mock.MagicMock(started=0, finished=100, code=200, sent=0, received=100),
        mock.MagicMock(started=0, finished=100, code=200, sent=0, received=100),
    ]
    return tracker

class ZeroQuantityRunner(runners.QuantityRunner):
    def run(self, *args):
        self._total = 0
        self._remaining = 0
        super(ZeroQuantityRunner, self).run(*args)

def zero_quantity_runner(*args):
    runner = runners.QuantityRunner(*args)
    runner._total = 0
    runner._remaining = 0
    return runner


@mock.patch("sys.stderr", new_callable=StringIO.StringIO)
@mock.patch("sys.exit", side_effect=ExitException)
class Function_main_Tests(unittest.TestCase):
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

    def test_run_without_flags(self, _, stderr):
        args = ["http://localhost:8080/"]

        with self.assertRaises(ExitException):
            main_.main(args)

        self.assertIn(
            "one of the arguments -n/--requests -d/--duration is required",
            stderr.getvalue())

    def test_with_usage_error(self, sys_exit, _):
        args = ["http://localhost:8080/", "-H foo"]

        with self.assertRaises(ExitException):
            main_.main(args)

        exit_call_arg = sys_exit.call_args[0][0]
        self.assertIn("usage:", exit_call_arg)

    def test_requests_run(self, *_):
        stdout = StringIO.StringIO()
        args = ["http://localhost:8080", "-n10", "--header", "Host:foo"]

        main_.main(args, stdout)

        self.assertRegexpMatches(stdout.getvalue(), self.OUTPUT_LINES_PATTERN)


class ParserTests(unittest.TestCase):
    def test_custom_headers(self):
        args = ["-Hfoo:bar", "-H", "baz:qux", "--header", "foobar:bazqux"]
        parser = main_.get_argument_parser()

        args = parser.parse_args(["http://localhost:8080/", "-n1"] + args)

        self.assertIn(("foo", "bar"), args.headers)
        self.assertIn(("baz", "qux"), args.headers)
        self.assertIn(("foobar", "bazqux"), args.headers)

    def test_invalid_header_arg(self):
        args = ["-H", "foo"]
        parser = main_.get_argument_parser()

        with self.assertRaises(main_.UsageError):
            args = parser.parse_args(["http://localhost:8080/", "-n1"] + args)

    def test_add_body_arg(self):
        args = ["-m", "POST", "-b", "foobarbaz"]
        parser = main_.get_argument_parser()

        args = parser.parse_args(["http://localhost:8080/", "-n1"] + args)

        self.assertEqual(args.body, "foobarbaz")

    def test_add_body_with_get(self):
        args = ["-b", "foobarbaz"]
        parser = main_.get_argument_parser()

        with self.assertRaises(main_.UsageError) as context:
            args = parser.parse_args(["http://localhost:8080/", "-n1"] + args)

        self.assertIn(
            "Cannot specify -b/--body with",
            context.exception.message)

    def test_add_duplicate_body(self):
        args = ["-m", "POST", "-b", "foobarbaz", "-b", "wibwobwub"]
        parser = main_.get_argument_parser()

        with self.assertRaises(main_.UsageError) as context:
            args = parser.parse_args(["http://localhost:8080/", "-n1"] + args)

        self.assertIn("more than once", context.exception.message)

    def test_use_custom_reporter(self):
        args = ["--reporter", "csv"]
        parser = main_.get_argument_parser()

        args = parser.parse_args(["http://localhost:8080/", "-n1"] + args)

        self.assertEqual(args.reporter_class, reporters.CSVReporter)
