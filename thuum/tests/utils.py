import mock
from tornado import (
    httpclient,
    testing,
    web,
)

class Base(testing.AsyncHTTPTestCase):
    def get_app(self):
        class Nothing(web.RequestHandler):
            def nothing(self):
                pass
            delete = get = head = options = post = put = nothing
        return web.Application([(r"/.*", Nothing)])

    def get_runner(self, runner_cls, client=None, make_request=None, **kwargs):
        client = client or self.http_client
        make_request = make_request or self.get_request
        runner = runner_cls(client, make_request, **kwargs)
        events = dict(
            ready=mock.MagicMock(),
            start=mock.MagicMock(),
            finish=mock.MagicMock(),
        )

        runner.events.on("request_ready", events["ready"])
        runner.events.on("request_started", events["start"])
        runner.events.on("request_finished", events["finish"])

        return events, runner

    def get_request(self, *args, **kwargs):
        return httpclient.HTTPRequest(
            self.get_url("/foo"),
            "GET",
            *args,
            **kwargs
        )
