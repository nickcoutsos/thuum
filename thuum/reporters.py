"""
Encoding of per-request results of a load test useful for further analysis.

"""

import abc
import collections
import csv
import json

from thuum import stats

FIELDS = (
    "started",
    "finished",
    "code",
    "sent",
    "received",
)

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


def filter_record(record):
    record = record.__dict__
    record = dict([(k, v) for k, v in record.iteritems() if k in FIELDS])
    return record

class BaseReporter(object):
    """
    Base class for turning `thuum.stats.Record` objects into textual reports.

    """
    __metaclass__ = abc.ABCMeta

    def progress(self, runner):
        """
        Display test progress for the given runner.

        """

    def record(self, record):
        """
        Add a record to the report.

        """

    def summarize(self, tracker):
        """
        Display a summary of the results collected by the given tracker.

        """


class TerminalReporter(BaseReporter):
    def __init__(self, stream):
        self.stream = stream

    def progress(self, runner):
        if self.stream.isatty():
            update = runner.progress()
            self.stream.write("\r")
            self.stream.write(PROGRESS_TEMPLATE.format(**update))
            self.stream.flush()

    def summarize(self, tracker):
        records = tracker.get_records()
        time_stats = stats.get_time_stats(records)

        self.stream.write("\n")
        if time_stats is None:
            self.stream.write("**No completed requests**")
            return

        self.stream.write(TIMING_REPORT_TEMPLATE.format(**time_stats) + "\n")

        codes = collections.Counter([r.code for r in records if r.code >= 300])
        for code, count in codes.iteritems():
            self.stream.write("[%d] responses: %d\n" % (code, count))


class CSVReporter(BaseReporter):
    """
    CSV formatted report of `thuum.stats.Record` objects.

    """
    def __init__(self, stream):
        self.writer = csv.DictWriter(stream, FIELDS)

    def record(self, record):
        record = filter_record(record)
        self.writer.writerow(record)


class JSONReporter(BaseReporter):
    """
    JSON encoded report of `thuum.stats.Record` objects and test summary.

    """
    def __init__(self, stream):
        self.stream = stream

    def record(self, record):
        record = filter_record(record)
        record = json.dumps(record, sort_keys=True)
        self.stream.write(record + "\n")
