import argparse
import functools
import sys

from tornado import (
    httpclient,
    ioloop,
)

def add_package_to_path():
    if not (__name__ == "__main__" and __package__ == ""):
        return
    import os
    sys.path.append(os.path.abspath(os.path.join(
        os.path.abspath(__file__),
        "..",
        "..")))

add_package_to_path()

from thuum import (
    runners,
    stats,
)

class UsageError(Exception):
    def __init__(self, message, parser):
        super(UsageError, self).__init__(message)
        self.parser = parser

class AddBody(argparse.Action):
    def __call__(self, parser, namespace, body, option_string=None):
        if namespace.body is not None:
            raise UsageError("Cannot specify -b/--body more than once.", parser)
        if namespace.method not in ("PATCH", "POST", "PUT"):
            raise UsageError(
                "Cannot specify -b/--body with %r." % namespace.method,
                parser)

        if body.startswith("py:"):
            pass
        elif body.startswith("@"):
            pass
        namespace.body = body

class AddHeader(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        header = tuple(values.split(":"))
        namespace.headers.append(header)
        if len(header) != 2:
            raise UsageError("Headers must be of the form 'name:value'", parser)


def get_argument_parser(parser=None):
    parser = parser or argparse.ArgumentParser(
        description="Simple HTTP Load runner.")

    parser.add_argument(
        "-m", "--method",
        choices=("DELETE", "GET", "HEAD", "OPTIONS", "POST", "PUT"),
        help="HTTP Method to use for request",
        default="GET")

    parser.add_argument(
        "-b", "--body",
        action=AddBody,
        default=None,
        help=(
            "Request body. Prefix with 'py:' to indicate a fully-qualified "
            "python callable. Prefix with '@' to indicate a file path."
        ))

    parser.add_argument(
        "-c", "--concurrency",
        help="Number of requests to make concurrently.",
        dest="concurrency",
        default=1,
        type=int)

    parser.add_argument(
        "-H", "--header", dest="headers",
        help="Custom header. name:value",
        default=[], action=AddHeader)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-n", "--requests",
        help="Number of requests",
        type=int)

    group.add_argument(
        "-d", "--duration",
        help="Run load test for specified length of time.",
        type=float)

    parser.add_argument("url", help="URL to hit")
    return parser


def main(argv=sys.argv[1:], stdout=sys.stdout, stderr=sys.stderr):
    parser = get_argument_parser()

    try:
        args = parser.parse_args(argv)
    except UsageError as exception:
        sys.exit("%s\n\n%s" % (
            exception.message,
            exception.parser.format_usage()
        ))

    httpclient.AsyncHTTPClient.configure(None, max_clients=args.concurrency)
    client = httpclient.AsyncHTTPClient(io_loop=ioloop.IOLoop.current())

    try:
        make_request = functools.partial(
            httpclient.HTTPRequest,
            args.url,
            args.method,
            args.headers,
            args.body)

        if args.duration:
            runner = runners.DurationRunner(client, make_request, args.duration)
        else:
            runner = runners.QuantityRunner(client, make_request, args.requests)

        tracker = stats.Tracker(runner)

        def progress():
            progress = runner.progress()
            stdout.write("\r")
            stdout.write(
                stats.PROGRESS_TEMPLATE.format(**progress))
            stdout.flush()

        client.io_loop.add_callback(progress)
        ioloop.PeriodicCallback(progress, 500, client.io_loop).start()
        runner.run()

        # One more progress call to ensure we're showing the final result.
        progress()

        stdout.write("\n")
        stats.print_results(tracker.get_records(), stdout)
        stats.print_errors(tracker.get_records(), stderr)

    except KeyboardInterrupt:
        sys.exit("Tests interrupted.")

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
