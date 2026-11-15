"""The page download (services/http_client.py) with mocked HTTP responses.

No test sends a real request: the client gets a fake session that answers
with prepared ``requests.Response`` objects, and a fake clock, so retries,
spacing and pauses take no real time. (Odoo's test framework also blocks
real outgoing requests.) The worker tests at the end run whole units through
the client, with the live-derived fixtures as page bodies.
"""

import io
from unittest.mock import patch

import requests
from requests.structures import CaseInsensitiveDict

from odoo.tests import TransactionCase, tagged

from ..services import http_client, reader, urls
from ..services.http_client import (FetchConnectionError, FetchTimeout, HttpStatusError, LoginPageError,
                                    PartnersHttpClient, RateLimitedError, RequestPacer,
                                    UnexpectedResponseError)
from .common import ANDORRA, ROAYATEC, fixture
from .test_worker import NOW, WorkerCase

ANDORRA_ID_URL = urls.listing_url("1")         # what the reader asks for
ANDORRA_SLUG_URL = ANDORRA[0]                  # where the site redirects
PAGE = "<html><head><title>Find Resellers | Odoo</title></head><body>ok</body></html>"


class FakeTime:
    """A clock and a sleep that only move when the client sleeps or a test says so."""

    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def clock(self):
        return self.now

    def wall(self):
        return 1_800_000_000.0 + self.now

    def sleep(self, seconds):
        self.sleeps.append(round(seconds, 3))
        self.now += seconds


class CutOffBody(io.BytesIO):
    """A body whose connection breaks after the first bytes."""

    def read(self, size=-1):
        if self.tell():
            raise requests.exceptions.ChunkedEncodingError("connection broken")
        return super().read(10)


class SlowBody(io.BytesIO):
    """A body that sends 1 KB every 11 seconds (of the fake clock)."""

    def __init__(self, fake_time):
        super().__init__(b"x" * 10_000)
        self.fake_time = fake_time

    def read(self, size=-1):
        self.fake_time.now += 11
        return super().read(1024)


def response(body=PAGE, status=200, headers=None, content_type="text/html; charset=utf-8", raw=None):
    """A factory of real requests.Response objects, one per request."""
    def make():
        answer = requests.Response()
        answer.status_code = status
        answer.headers = CaseInsensitiveDict({"Content-Type": content_type, **(headers or {})})
        data = body.encode("utf-8") if isinstance(body, str) else body
        answer.raw = raw() if raw else io.BytesIO(data)
        return answer
    return make


def redirect(location, status=301):
    return response("", status=status, headers={"Location": location})


class FakeSession:
    """Stands in for requests.Session: each URL answers with its queued answers, in order.

    The last answer of a URL repeats. An answer is a response factory or an
    exception instance to raise. Every call is recorded with its arguments.
    """

    def __init__(self, answers):
        self.answers = {url: list(items) for url, items in answers.items()}
        self.headers = {}
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        queue = self.answers.get(url)
        if not queue:
            raise AssertionError(f"unexpected request {url}")
        answer = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(answer, BaseException):
            raise answer
        return answer()

    def urls(self):
        return [url for url, _kwargs in self.calls]


def site_answers(pages):
    """Answers for saved pages: {asked URL: (final URL, fixture)} -> a redirect when they differ."""
    answers = {}
    for asked, (final, name) in pages.items():
        body = response(fixture(name))
        if final != asked:
            answers[asked] = [redirect(final.removeprefix(urls.SITE))]
        answers[final] = [body]
    return answers


@tagged("post_install", "-at_install")
class TestHttpClient(TransactionCase):
    """TP-PM-07 at the download layer: every failure raises, nothing becomes an empty page."""

    def setUp(self):
        super().setUp()
        self.time = FakeTime()
        self.pacer = RequestPacer(clock=self.time.clock, sleep=self.time.sleep, wall_clock=self.time.wall)

    def client(self, answers, pacer=None):
        session = FakeSession(answers)
        client = PartnersHttpClient(session=session, pacer=pacer or self.pacer, sleep=self.time.sleep,
                                    clock=self.time.clock)
        return client, session

    # ---------------------------------------------------------------- success

    def test_a_page_comes_back_with_its_final_url(self):
        client, session = self.client(site_answers({ANDORRA_ID_URL: ANDORRA}))
        pages = reader.read_country_listing(client, "1")
        # The reader's contract: the final URL after the redirect, and the text.
        self.assertEqual(len(pages), 1)
        self.assertEqual((pages[0].scope, pages[0].source_url), ("country", ANDORRA_SLUG_URL))
        self.assertEqual(len(pages[0].partners), 2)
        self.assertEqual(session.urls(), [ANDORRA_ID_URL, ANDORRA_SLUG_URL])
        for _url, kwargs in session.calls:
            self.assertEqual(kwargs, {"timeout": (5, 20), "allow_redirects": False, "stream": True})
        self.assertEqual(session.headers["User-Agent"], http_client.USER_AGENT)
        self.assertTrue(session.headers["Accept-Language"].startswith("en"))
        # Regression (Stage 10 live check): offering "deflate", the requests
        # default, made the site close the connection without a reply.
        self.assertEqual(session.headers["Accept-Encoding"], "gzip")
        self.assertEqual([entry["status"] for entry in client.log], [301, 200])
        self.assertEqual(client.log[1]["bytes"], len(fixture(ANDORRA[1]).encode()))
        # The redirect is a request too: it waited the minimum spacing.
        self.assertEqual(self.time.sleeps, [3.0])

    def test_requests_are_spaced_across_clients_of_the_process(self):
        first, _session = self.client({ANDORRA_SLUG_URL: [response()]})
        second, _session = self.client({ANDORRA_SLUG_URL: [response()]})
        first(ANDORRA_SLUG_URL)
        self.time.now += 1.0
        second(ANDORRA_SLUG_URL)
        self.assertEqual(self.time.sleeps, [2.0])

    # ---------------------------------------------------------------- URL rules

    def test_disallowed_urls_are_never_requested(self):
        client, session = self.client({})
        for url in ("https://www.odoo.com/partners/acme-1?country_id=1",
                    "https://www.odoo.com/partners/country/1/page/2/x",
                    "http://www.odoo.com/partners/country/1",
                    "https://example.com/partners/country/1"):
            with self.subTest(url=url), self.assertRaisesRegex(UnexpectedResponseError, "not requested"):
                client(url)
        self.assertEqual(session.calls, [])

    def test_redirect_targets_are_checked_before_they_are_followed(self):
        targets = {
            "https://www.odoo.com/partners?country_id=1": "robots.txt disallows URLs with country_id",
            "https://www.example.com/partners/country/1": "only https://www.odoo.com is fetched",
            "http://www.odoo.com/partners/country/andorra-1": "only https://www.odoo.com is fetched",
        }
        for target, reason in targets.items():
            client, session = self.client({ANDORRA_ID_URL: [redirect(target)]})
            with self.subTest(target=target), self.assertRaisesRegex(UnexpectedResponseError, reason):
                client(ANDORRA_ID_URL)
            self.assertEqual(session.urls(), [ANDORRA_ID_URL])

    def test_endless_redirects_stop(self):
        a, b = urls.listing_url("1"), urls.listing_url("2")
        client, session = self.client({a: [redirect(b)], b: [redirect(a)]})
        with self.assertRaisesRegex(UnexpectedResponseError, "more than 5 redirects"):
            client(a)
        self.assertEqual(len(session.calls), 6)

    # ---------------------------------------------------------------- login and rate limits

    def test_login_pages_are_failures_never_empty_results(self):
        login = "/web/login?redirect=%2Fpartners%2Fcountry%2F1"
        client, session = self.client({ANDORRA_ID_URL: [redirect(login, status=303)]})
        with self.assertRaisesRegex(LoginPageError, "redirected to a login page"):
            reader.read_country_listing(client, "1")
        self.assertEqual(session.urls(), [ANDORRA_ID_URL])  # the login page is not requested
        form = '<html><body><form><input type="password" name="password"/></form></body></html>'
        client, _session = self.client({ANDORRA_ID_URL: [response(form)]})
        with self.assertRaisesRegex(LoginPageError, "login page"):
            reader.read_country_listing(client, "1")

    def test_a_rate_limit_pauses_every_client_of_the_process(self):
        client, session = self.client({ANDORRA_ID_URL: [response("", status=429, headers={"Retry-After": "120"})]})
        with self.assertRaises(RateLimitedError) as caught:
            client(ANDORRA_ID_URL)
        self.assertEqual((caught.exception.status, caught.exception.retry_after), (429, 120))
        self.assertEqual(len(session.calls), 1)  # never retried at once
        self.assertIn("asked to slow down", client.paused_reason())
        # While paused, no client of the process sends anything.
        other, other_session = self.client({ANDORRA_SLUG_URL: [response()]})
        with self.assertRaisesRegex(RateLimitedError, "not requested"):
            other(ANDORRA_SLUG_URL)
        self.assertEqual(other_session.calls, [])
        # The pause lasts at least 10 minutes, even when Retry-After is shorter.
        self.time.now += 599
        self.assertTrue(other.paused_reason())
        self.time.now += 2
        self.assertIsNone(other.paused_reason())
        self.assertEqual(other(ANDORRA_SLUG_URL), (ANDORRA_SLUG_URL, PAGE))

    def test_other_rate_limit_answers(self):
        cases = {
            # A Retry-After date about a year ahead: the pause is capped at 24 hours.
            "503 with Retry-After": (response("", status=503, headers={"Retry-After": "Fri, 31 Dec 2027 23:59:59 GMT"}),
                                     24 * 3600),
            "a Too Many Requests page": (response("<html><head><title>429 Too Many Requests</title></head></html>"),
                                         600),
        }
        for label, (answer, pause) in cases.items():
            pacer = RequestPacer(clock=self.time.clock, sleep=self.time.sleep, wall_clock=self.time.wall)
            client, _session = self.client({ANDORRA_SLUG_URL: [answer]}, pacer=pacer)
            with self.subTest(label):
                with self.assertRaises(RateLimitedError):
                    client(ANDORRA_SLUG_URL)
                self.assertTrue(pacer.paused_reason())
                self.assertEqual(pacer.paused_until - self.time.wall(), pause)

    # ---------------------------------------------------------------- HTTP errors and retries

    def test_http_errors_fail_and_only_transient_ones_are_retried(self):
        for status, tries in ((404, 1), (403, 1), (500, 1), (502, 3), (503, 3), (504, 3)):
            client, session = self.client({ANDORRA_SLUG_URL: [response("error", status=status)]})
            with self.subTest(status=status), self.assertRaisesRegex(HttpStatusError, f"HTTP {status}"):
                client(ANDORRA_SLUG_URL)
            self.assertEqual(len(session.calls), tries)
        # The retries wait 2 s then 4 s, besides the request spacing.
        self.time.sleeps.clear()
        client, session = self.client({ANDORRA_SLUG_URL: [response("bad gateway", status=502), response()]})
        self.time.now += 10
        self.assertEqual(client(ANDORRA_SLUG_URL), (ANDORRA_SLUG_URL, PAGE))
        self.assertEqual(len(session.calls), 2)
        self.assertIn(2, self.time.sleeps)

    def test_timeouts_and_cut_off_pages_are_retried_then_fail(self):
        failures = {
            FetchTimeout: [requests.exceptions.ConnectTimeout("connect")],
            FetchConnectionError: [requests.exceptions.ConnectionError("refused")],
        }
        for error, answers in failures.items():
            client, session = self.client({ANDORRA_SLUG_URL: answers})
            with self.subTest(error=error.__name__), self.assertRaises(error):
                client(ANDORRA_SLUG_URL)
            self.assertEqual(len(session.calls), 3)
        client, session = self.client({ANDORRA_SLUG_URL: [response(raw=lambda: CutOffBody(PAGE.encode()))]})
        with self.assertRaisesRegex(FetchConnectionError, "cut off"):
            client(ANDORRA_SLUG_URL)
        self.assertEqual(len(session.calls), 3)
        # A timeout followed by an answer is not a failure.
        client, session = self.client({ANDORRA_SLUG_URL: [requests.exceptions.ReadTimeout("slow"), response()]})
        self.assertEqual(client(ANDORRA_SLUG_URL), (ANDORRA_SLUG_URL, PAGE))

    def test_a_page_that_takes_too_long_to_read_is_a_timeout(self):
        client, session = self.client({ANDORRA_SLUG_URL: [response(raw=lambda: SlowBody(self.time))]})
        with self.assertRaisesRegex(FetchTimeout, "more than 30 s"):
            client(ANDORRA_SLUG_URL)
        self.assertEqual(len(session.calls), 3)

    # ---------------------------------------------------------------- bodies

    def test_unusable_bodies_are_failures(self):
        big = b"x" * (http_client.MAX_BYTES + 1)
        cases = {
            "page of 9999999 bytes": response(headers={"Content-Length": "9999999"}),
            "page larger than": response(big),
            r"not an HTML page \(application/json\)": response("{}", content_type="application/json"),
            "empty page": response("  \n "),
            "HTTP 204 is not a page": response("", status=204),
        }
        for message, answer in cases.items():
            client, session = self.client({ANDORRA_SLUG_URL: [answer]})
            with self.subTest(message), self.assertRaisesRegex(UnexpectedResponseError, message):
                client(ANDORRA_SLUG_URL)
            self.assertEqual(len(session.calls), 1)

    def test_text_is_decoded_with_the_announced_charset(self):
        latin = "<html><body>Bogot\xe1</body></html>"
        client, _session = self.client({ANDORRA_SLUG_URL: [
            response(latin.encode("latin-1"), content_type="text/html; charset=ISO-8859-1")]})
        self.assertEqual(client(ANDORRA_SLUG_URL)[1], latin)
        self.assertEqual(http_client._charset("text/html; charset=no-such-codec"), "utf-8")
        self.assertEqual(http_client.retry_after_seconds("120", 0), 120)
        self.assertEqual(http_client.retry_after_seconds("Thu, 01 Jan 1970 00:02:00 GMT", 0), 120)
        self.assertIsNone(http_client.retry_after_seconds("soon", 0))


@tagged("post_install", "-at_install")
class TestWorkerWithHttpClient(WorkerCase):
    """Whole units through the HTTP client: the fixtures as bodies, failures as failed units."""

    def setUp(self):
        super().setUp()
        self.time = FakeTime()
        self.pacer = RequestPacer(clock=self.time.clock, sleep=self.time.sleep, wall_clock=self.time.wall)

    def client(self, answers):
        return PartnersHttpClient(session=FakeSession(answers), pacer=self.pacer, sleep=self.time.sleep,
                                  clock=self.time.clock)

    def test_units_read_pages_through_the_client(self):
        partners = self.egypt_partners()
        roayatec = partners[17207720]
        run = self.Run.create({"trigger": "manual"})
        andorra_unit = self.queue("country_partners", self.andorra, run)
        page_unit = self.queue("partner_details", roayatec, run)
        client = self.client(site_answers({ANDORRA_ID_URL: ANDORRA, ROAYATEC[0]: ROAYATEC}))
        result = self.process(client, max_units=2)
        self.assertEqual(sorted(result["done"]), sorted((andorra_unit | page_unit).ids))
        self.assertEqual(self.partner(22015187).country_id, self.andorra)
        self.assertEqual(len(roayatec.reference_ids), 3)
        self.assertEqual([entry["status"] for entry in client.log], [301, 200, 200])

    def test_a_login_page_fails_the_unit_and_keeps_the_data(self):
        earlier = self.earlier_partner(self.andorra, 990001)
        unit = self.queue("country_partners", self.andorra)
        client = self.client({ANDORRA_ID_URL: [redirect("/web/login?redirect=%2Fpartners", status=303)]})
        result = self.process(client)
        self.assertEqual(result["failed"], unit.ids)
        self.assertRecordValues(unit, [{"state": "pending", "attempt_count": 1}])
        self.assertTrue(earlier.active)  # a failed read archives nothing
        error = self.SyncError.search([("work_item_id", "=", unit.id)])
        self.assertRecordValues(error, [{"error_class": "LoginPageError", "url": ANDORRA_ID_URL}])

    def test_a_rate_limit_stops_the_batch_and_keeps_the_queue(self):
        earlier = self.earlier_partner(self.andorra, 990002)
        run = self.Run.create({"trigger": "manual"})
        andorra = self.queue("country_partners", self.andorra, run)
        others = self.queue("country_partners", self.anguilla, run) | self.queue("country_partners", self.egypt, run)
        client = self.client({ANDORRA_ID_URL: [response("", status=429, headers={"Retry-After": "900"})]})
        result = self.process(client, max_units=10)
        # One unit met the limit and has a counted try; the batch stopped there.
        self.assertEqual((result["failed"], result["done"], result["waiting"]), (andorra.ids, [], True))
        self.assertEqual(len(client.session.calls), 1)
        self.assertRecordValues(andorra, [{"state": "pending", "attempt_count": 1}])
        self.assertRecordValues(others, [{"state": "pending", "attempt_count": 0}] * 2)
        self.assertTrue(earlier.active)
        self.assertIn("asked to slow down", run.waiting_reason)
        self.assertEqual(self.SyncError.search([("work_item_id", "=", andorra.id)]).error_class,
                         "RateLimitedError")
        # The next batch, with a new client of the same process, sends nothing.
        later = self.client({})
        result = self.process(later, now=NOW, max_units=10)
        self.assertEqual((result["processed"], result["waiting"]), (0, True))
        self.assertEqual(later.session.calls, [])
        # The scheduler is told that nothing was done, so it does not loop.
        Worker = type(self.Worker)
        with patch.object(Worker, "_get_page_source", lambda worker: later), \
                patch.object(type(self.env["ir.cron"]), "_notify_progress") as notify:
            with self.mock_mail_gateway(), self.assertLogs("odoo.addons.azk_odoo_partner_monitor.models.worker",
                                                           "WARNING"):
                self.Worker._cron_process_queue()
        self.assertEqual(notify.call_args.kwargs["done"], 0)
