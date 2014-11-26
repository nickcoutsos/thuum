import collections
import math
import sys

TIMING_REPORT_TEMPLATE = """\
Requests    {count:10}
Duration    {dur:>10.4f}s
Average     {avg:>10.4f}s
Fastest     {min:>10.4f}s
Slowest     {max:>10.4f}s
Deviation   {dev:>10.4f}
RPS         {rps:>10.2f}"""

def get_time_stats(responses, duration):
    times = [r.request_time for r in responses]
    total = sum(times)
    count = len(times)

    stats = {
        "count": count,
        "dur": duration,
        "avg": total / float(count),
        "min": min(times),
        "max": max(times),
        "rps": count / float(duration)
    }
    stats["dev"] = math.sqrt(
        sum(
            (t - stats["avg"]) ** 2
            for t in times
        ) / count)

    return stats

def print_results(responses, duration, stream=sys.stdout):
    stats = get_time_stats(responses, duration)
    stream.write(TIMING_REPORT_TEMPLATE.format(**stats) + "\n")

def print_errors(responses, stream=sys.stderr):
    codes = collections.Counter([r.code for r in responses if r.error])
    for code, count in codes.iteritems():
        stream.write("%d errors: %d\n" % (code, count))
