"""Page download for the Odoo Partners website: the ``fetch(url)`` of services/reader.py.

``PartnersHttpClient`` is callable: ``client(url)`` returns ``(final_url, html)``
for one public page of https://www.odoo.com, or RAISES a ``FetchError``. A
failed download therefore never looks like an empty page, and the reader and
the worker never store anything for that scope (docs/resilience.md).

Bounds, all fixed here (the worker bounds the number of pages per batch):

- timeouts: 5 s to connect, 20 s between two received bytes, and at most
  30 s to read one page;
- size: at most 3 MB per page (the live pages were 70 to 390 KB);
- rate: at least 3 s between two requests of this process, redirects
  included, shared by every client of the process (the worker creates one
  client per batch, and the scheduler may run several batches in a row);
- retries: at most 3 tries of one URL, 2 s then 4 s apart, and only for a
  timeout, a connection error, a cut-off page, or HTTP 502, 503 or 504.
  Nothing else is retried here: the worker retries a failed unit later,
  with its own backoff (models/common.py, retry_delay);
- redirects: followed one by one, at most 5. Each target is checked
  against the URL rules (services/urls.py, fetch_allowed: www.odoo.com over
  HTTPS only, and the robots.txt rules) BEFORE it is requested.

Failures, each a FetchError subclass carrying the URL:

- FetchTimeout, FetchConnectionError: the network, or a page cut off;
- HttpStatusError: an HTTP error status not listed below;
- RateLimitedError: HTTP 429, a 503 with Retry-After, or a "Too Many
  Requests" page. The process then pauses: every later call raises at once,
  without contacting the site, until the pause ends (the Retry-After delay,
  at least 10 minutes, at most 24 hours);
- LoginPageError: a redirect to the login page, or a page with a password
  field (the public pages have none);
- UnexpectedResponseError: anything else that is not a usable page: not
  HTML, empty, larger than the limit, too many redirects, or a redirect off
  the site or to a URL that robots.txt disallows.
"""

import codecs
import logging
import re
import threading
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urljoin, urlsplit

import requests

from . import urls

_logger = logging.getLogger(__name__)

# No personal data: the client identifies the software only.
USER_AGENT = "azk_odoo_partner_monitor/18.0 (Odoo module; reads the public partner directory)"
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml",
    # The parsers read the English labels (D-26).
    "Accept-Language": "en-US,en;q=0.8",
    # gzip only. Offered "deflate" too (the requests default, "gzip,
    # deflate"), the site closed HTTP/1.1 connections without any reply after
    # about 15 seconds; found by the Stage 10 live check (docs/review_findings.md).
    "Accept-Encoding": "gzip",
}
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 20
MAX_READ_SECONDS = 30
MAX_BYTES = 3 * 1024 * 1024
MIN_INTERVAL = 3.0
MAX_TRIES = 3
RETRY_DELAYS = (2, 4)
MAX_REDIRECTS = 5
DEFAULT_PAUSE = 600
MAX_PAUSE = 24 * 3600
RETRYABLE_STATUSES = frozenset({502, 503, 504})
HTML_TYPES = frozenset({"text/html", "application/xhtml+xml"})
_LOGIN_PATH = re.compile(r"/web/(?:login|signup|reset_password)(?:/|$)")
_PASSWORD_FIELD = re.compile(r"<input\b[^>]*\btype\s*=\s*[\"']?password\b", re.IGNORECASE)
_RATE_LIMIT_TITLE = re.compile(r"<title[^>]*>[^<]*(?:too many requests|rate limit)", re.IGNORECASE)


class FetchError(Exception):
    """A page could not be downloaded. Never a valid empty result."""

    def __init__(self, message, url=None, status=None):
        super().__init__(f"{message} [{url}]" if url else message)
        self.url = url
        self.status = status


class FetchTimeout(FetchError):
    """No answer, or no complete page, within the time limits."""


class FetchConnectionError(FetchError):
    """The connection failed, or the page was cut off."""


class HttpStatusError(FetchError):
    """The site answered with an HTTP error status."""


class RateLimitedError(FetchError):
    """The site asked the client to slow down, or the client is paused because it did."""

    def __init__(self, message, url=None, status=None, retry_after=None):
        super().__init__(message, url, status)
        self.retry_after = retry_after


class LoginPageError(FetchError):
    """The site answered with a login page instead of the public page."""


class UnexpectedResponseError(FetchError):
    """The answer is not a usable page of the site."""


def retry_after_seconds(value, now):
    """Seconds asked by a Retry-After header (a number or an HTTP date), else None."""
    value = (value or "").strip()
    if not value:
        return None
    if value.isdigit():
        return int(value)
    try:
        moment = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return max(0, int(moment.timestamp() - now))


def _charset(content_type):
    """The charset named in a Content-Type header, if Python knows it, else UTF-8."""
    for parameter in content_type.split(";")[1:]:
        name, _sep, value = parameter.partition("=")
        if name.strip().lower() == "charset":
            value = value.strip().strip("\"'")
            try:
                return codecs.lookup(value).name
            except LookupError:
                break
    return "utf-8"


class RequestPacer:
    """Spaces the requests of a process and holds its pause after a rate limit.

    One instance (DEFAULT_PACER) serves every client of the process, so the
    spacing and the pause outlive one worker batch. Each process has its
    own: in multi-process mode, two cron workers each keep their spacing.
    """

    def __init__(self, min_interval=MIN_INTERVAL, clock=time.monotonic, sleep=time.sleep,
                 wall_clock=time.time):
        self.min_interval = min_interval
        self.clock = clock
        self.sleep = sleep
        self.wall_clock = wall_clock
        self._lock = threading.Lock()
        self._next_at = None
        self.paused_until = None  # wall-clock timestamp, or None

    def wait(self):
        """Block until the next request may start, and book the slot after it."""
        with self._lock:
            now = self.clock()
            if self._next_at is not None and self._next_at > now:
                self.sleep(self._next_at - now)
                now = max(now, self._next_at)
            self._next_at = now + self.min_interval

    def pause(self, seconds):
        """Stop every request of the process for ``seconds`` (at least 10 minutes, at most 24 hours)."""
        seconds = min(max(seconds or 0, DEFAULT_PAUSE), MAX_PAUSE)
        with self._lock:
            until = self.wall_clock() + seconds
            self.paused_until = max(self.paused_until or until, until)

    def paused_reason(self):
        """A text saying until when downloads are paused, or None."""
        with self._lock:
            if self.paused_until is None:
                return None
            if self.wall_clock() >= self.paused_until:
                self.paused_until = None
                return None
            until = datetime.fromtimestamp(self.paused_until, timezone.utc)
        return ("the Odoo website asked to slow down (rate limit); downloads resume after "
                f"{until:%Y-%m-%d %H:%M} UTC")


DEFAULT_PACER = RequestPacer()


class PartnersHttpClient:
    """A ``fetch(url)`` for services/reader.py that downloads public pages of www.odoo.com.

    ``log`` keeps one entry per HTTP request (URL, status, bytes read,
    seconds), redirects and retries included.
    """

    def __init__(self, session=None, pacer=None, sleep=time.sleep, clock=time.monotonic):
        self.session = session if session is not None else self._new_session()
        self.session.headers.update(REQUEST_HEADERS)
        self.pacer = pacer or DEFAULT_PACER
        self.sleep = sleep
        self.clock = clock
        self.log = []

    @staticmethod
    def _new_session():
        session = requests.Session()
        # The website keeps the visitor's language in this cookie.
        session.cookies.set("frontend_lang", "en_US", domain=urls.PARTNERS_HOST)
        return session

    def __call__(self, url):
        return self.get(url)

    def paused_reason(self):
        """Why no request may be sent now (after a rate limit), or None."""
        return self.pacer.paused_reason()

    def get(self, url):
        """Return ``(final_url, html)`` for ``url``, following redirects, or raise FetchError."""
        reason = urls.fetch_allowed(url)
        if reason:
            raise UnexpectedResponseError(f"not requested: {reason}", url)
        current = url
        for _hop in range(MAX_REDIRECTS + 1):
            location, text = self._download(current)
            if location is None:
                self._check_page(current, text)
                return current, text
            target = urljoin(current, location)
            if _LOGIN_PATH.search(urlsplit(target).path):
                raise LoginPageError(f"redirected to a login page ({target})", url)
            reason = urls.fetch_allowed(target)
            if reason:
                raise UnexpectedResponseError(f"redirect to {target} refused: {reason}", url)
            current = target
        raise UnexpectedResponseError(f"more than {MAX_REDIRECTS} redirects", url)

    # ------------------------------------------------------------------
    # One URL, with bounded retries
    # ------------------------------------------------------------------

    def _download(self, url):
        """Return (redirect location, None) or (None, page text) for one URL."""
        for attempt in range(1, MAX_TRIES + 1):
            try:
                return self._attempt(url)
            except FetchError as error:
                if not self._retryable(error) or attempt == MAX_TRIES:
                    raise
                delay = RETRY_DELAYS[attempt - 1]
                _logger.info("Partner Monitor: %s; try %s of %s again in %s s.",
                             error, attempt + 1, MAX_TRIES, delay)
                self.sleep(delay)
        raise AssertionError("unreachable")

    @staticmethod
    def _retryable(error):
        if isinstance(error, (FetchTimeout, FetchConnectionError)):
            return True
        return type(error) is HttpStatusError and error.status in RETRYABLE_STATUSES

    def _attempt(self, url):
        reason = self.pacer.paused_reason()
        if reason:
            raise RateLimitedError(f"not requested: {reason}", url)
        self.pacer.wait()
        started = self.clock()
        entry = {"url": url, "status": None, "bytes": 0, "seconds": None}
        self.log.append(entry)
        try:
            try:
                response = self.session.get(url, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                                            allow_redirects=False, stream=True)
            except requests.Timeout as exc:
                raise FetchTimeout(f"no answer in time ({exc.__class__.__name__})", url) from exc
            except requests.RequestException as exc:
                raise FetchConnectionError(f"connection failed ({exc.__class__.__name__})", url) from exc
            with response:
                entry["status"] = response.status_code
                if response.is_redirect:
                    return response.headers["Location"], None
                self._check_status(url, response)
                body = self._read_body(url, response, started)
                entry["bytes"] = len(body)
                return None, self._decode(url, response, body)
        finally:
            entry["seconds"] = round(self.clock() - started, 3)

    def _check_status(self, url, response):
        status = response.status_code
        if status == 200:
            return
        retry_after = retry_after_seconds(response.headers.get("Retry-After"), self.pacer.wall_clock())
        if status == 429 or (status == 503 and retry_after is not None):
            self.pacer.pause(retry_after)
            raise RateLimitedError(f"HTTP {status}: the website limits the request rate", url,
                                   status, retry_after)
        if status >= 400:
            raise HttpStatusError(f"HTTP {status}", url, status)
        raise UnexpectedResponseError(f"HTTP {status} is not a page", url, status)

    def _read_body(self, url, response, started):
        length = response.headers.get("Content-Length", "")
        if length.isdigit() and int(length) > MAX_BYTES:
            raise UnexpectedResponseError(f"page of {length} bytes, more than {MAX_BYTES}", url)
        chunks, size = [], 0
        try:
            for chunk in response.iter_content(chunk_size=64 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise UnexpectedResponseError(f"page larger than {MAX_BYTES} bytes", url)
                if self.clock() - started > MAX_READ_SECONDS:
                    raise FetchTimeout(f"the page took more than {MAX_READ_SECONDS} s to read", url)
                chunks.append(chunk)
        except requests.RequestException as exc:
            raise FetchConnectionError(f"the page was cut off ({exc.__class__.__name__})", url) from exc
        return b"".join(chunks)

    @staticmethod
    def _decode(url, response, body):
        content_type = response.headers.get("Content-Type", "")
        if content_type.split(";")[0].strip().lower() not in HTML_TYPES:
            raise UnexpectedResponseError(f"not an HTML page ({content_type or 'no content type'})", url)
        text = body.decode(_charset(content_type), errors="replace")
        if not text.strip():
            raise UnexpectedResponseError("empty page", url)
        return text

    def _check_page(self, url, text):
        """Refuse a login or rate-limit page served with HTTP 200."""
        if _PASSWORD_FIELD.search(text):
            raise LoginPageError("the website answered with a login page", url)
        if _RATE_LIMIT_TITLE.search(text):
            self.pacer.pause(DEFAULT_PAUSE)
            raise RateLimitedError("the website answered with a rate-limit page", url, 200)
