# Thu'um [![Build Status](https://travis-ci.org/nickcoutsos/thuum.svg)](https://travis-ci.org/nickcoutsos/thuum) [![Coverage Status](https://coveralls.io/repos/nickcoutsos/thuum/badge.svg?branch=master)](https://coveralls.io/r/nickcoutsos/thuum?branch=master)

*(or `thuum`)*


Thu'um is a port of [tarekziade/boom](https://github.com/tarekziade/boom) that
has been rewritten to use [Tornado](https://github.com/tornadoweb/tornado) to
provide concurrency and http client instead of gevent and requests, thus only
requiring a single thread for execution.

> **Boom!** is a simple command line tool to send some load to a web app.

> *Boom!* is a script you can use to quickly smoke-test your
web app deployment. If you need a more complex tool,
I'd suggest looking at `[Funkload](http://funkload.nuxeo.org/)`.

> *Boom!* was specifically written to replace my Apache Bench usage,
to provide a few missing features and fix a few annoyances I had
with AB.

Using *Tornado* async requests instead of greenlets isn't a decision related
to performance, just curiosity. But apparently the performance is good, too.

## Name

from [UESP lore:Thu'um](http://www.uesp.net/wiki/Lore:Thu'um):
> The thu'um, also called the Storm Voice or simply the Voice, is a form of
magic inherent in most Nords and some others which uses the words of the
language of the Dragons to form "Shouts", the equivalent of spells, of immense
power.

Thuum is the power of *Boom!* with the forceful winds of a tornado.

## Installation

    pip install https://github.com/nickcoutsos/thuum/

I guess.

*Thu'um* requires `tornado>=4.0`, and `pyee`, and currently only supports
Python2.7 because I've yet to dive into Python 3 and do not acknowledge 2.6.


## Basic usage

Basic usage example: 10000 requests with a maximum concurrency of 20 users:

    $ thuum -n 10000 -c 20 http://localhost:8000/
    Requests         10000
    Duration      113.6654s
    Average         0.2249s
    Fastest         0.0028s
    Slowest         3.9670s
    Deviation       0.4345
    RPS              87.98
    599 errors: 28

## Changes from *Boom!*

The output format has changed considerably. Other feature changes:

* you can still send any number of requests with any level of concurrency
* you **cannot** specify the "quiet" option
* you **cannot** specify pre- and post-hooks for the requests and responses.
* you **cannot** generate the request body via
* you **absolutely cannot** cause dragons to fall from the sky.

Much of the actual test running and reporting has been refactored out of the
script itself, so it's possible do implement your own custom test program with
functionality from `thuum.runners` and `thuum.stats`... perhaps not completely
dissimilar to what would be required to dynamically generate the requests.

There's more to come.
