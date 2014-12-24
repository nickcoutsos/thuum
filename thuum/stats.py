import collections
import math
import sys
import time

PROGRESS_TEMPLATE = "[{current:.1f}/{total:.1f} {unit}] {percentage:.1f}%"

TIMING_REPORT_TEMPLATE = """\
Requests    {count:10}
Duration    {dur:>15.4f}s
Average     {avg:>15.4f}s
Fastest     {min:>15.4f}s
Slowest     {max:>15.4f}s
Deviation   {dev:>15.4f}
Received    {received:>10}B
RPS         {rps:>13.2f}"""


class Record(object):
    def __init__(self):
        self.started = None
        self.finished = None
        self.code = None
        self.sent = 0
        self.received = 0

    def on_received(self, chunk):
        self.received += len(chunk)

    def start(self):
        self.started = time.time()

    def complete(self, future):
        response = future.result()
        self.finished = time.time()
        self.code = response.code


class Tracker(object):
    def __init__(self, runner=None):
        self.started = None
        self.finished = None
        self.requests = 0
        self._pending = {}
        self._records = []

        if runner:
            self._attach_to(runner)

    def _attach_to(self, runner):
        runner.events.on("tests_started", self.tests_started)
        runner.events.on("tests_finished", self.tests_finished)
        runner.events.on("request_ready", self.request_ready)
        runner.events.on("request_started", self.request_started)
        runner.events.on("request_finished", self.request_finished)

    def get_records(self):
        return self._records

    def tests_started(self):
        self.started = time.time()

    def tests_finished(self):
        self.finished = time.time()

    def request_ready(self, future, request):
        record = Record()
        request.streaming_callback = record.on_received
        self._pending[future] = record
        self._records.append(record)

    def request_started(self, future):
        self._pending[future].start()

    def request_finished(self, future):
        record = self._pending.pop(future)
        record.complete(future)


def standard_deviation(values):
    count = float(len(values))
    average = sum(values) / count
    return math.sqrt(
        sum(
            (v - average) ** 2
            for v in values
        ) / count)

def get_time_stats(results):
    completed = [r for r in results if r.finished is not None]

    if len(completed) == 0:
        return None

    times = [r.finished - r.started for r in completed]
    total = sum(times)
    count = len(times)
    received = sum(r.received for r in completed)
    duration = (
        max(r.finished for r in completed)
        -min(r.started for r in completed)
    )

    stats = {
        "count": count,
        "dur": duration,
        "avg": total / float(count),
        "min": min(times),
        "max": max(times),
        "rps": count / float(duration),
        "received": received,
        "dev": standard_deviation(times),
    }

    return stats

def print_results(results, stream=sys.stdout):
    stats = get_time_stats(results)
    if stats is None:
        stream.write("**No completed requests**")
        return
    stream.write(TIMING_REPORT_TEMPLATE.format(**stats) + "\n")

def print_errors(results, stream=sys.stderr):
    codes = collections.Counter([
        r.code for r in results
        if r.code >= 300
    ])

    for code, count in codes.iteritems():
        stream.write("%d errors: %d\n" % (code, count))
