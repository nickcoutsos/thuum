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
Received    {received:>10}B
RPS         {rps:>10.2f}"""

def get_time_stats(results):
    times = [r.finish - r.start for r in results]
    total = sum(times)
    count = len(times)
    received = sum(r.received for r in results)
    duration = (
        max(r.finish for r in results)
        -min(r.start for r in results)
    )

    stats = {
        "count": count,
        "dur": duration,
        "avg": total / float(count),
        "min": min(times),
        "max": max(times),
        "rps": count / float(duration),
        "received": received,
    }
    stats["dev"] = math.sqrt(
        sum(
            (t - stats["avg"]) ** 2
            for t in times
        ) / count)

    return stats

def print_results(results, stream=sys.stdout):
    stats = get_time_stats(results)
    stream.write(TIMING_REPORT_TEMPLATE.format(**stats) + "\n")

def print_errors(results, stream=sys.stderr):
    codes = collections.Counter([
        r.code for r in results
        if r.code >= 300
    ])

    for code, count in codes.iteritems():
        stream.write("%d errors: %d\n" % (code, count))
