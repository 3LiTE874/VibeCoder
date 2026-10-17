"""One public web note. Used only while Zira is ONLINE, then saved in her database."""

from __future__ import annotations

import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import parse_qs, quote_plus, unquote, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from vibecoder.zira_memory import save_note

_AGENT = "VibeCoder/0.1.0 (personal local editor; public reference lookup)"
_SEARCH = "https://lite.duckduckgo.com/lite/"
_MAX_BYTES = 400_000
_NOTE_CHARS = 1200


class _PublicRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def lookup_web(query: str) -> str:
    topic = " ".join(query.split())
    if not topic:
        return "That lookup needs a topic."
    try:
        hits = _search(topic)
        if not hits:
            return "No public page came back for that."
        page_url, excerpt = _read_page(hits[0][1])
    except OSError as exc:
        return f"The lookup did not complete: {exc}"
    lines = [hits[0][0], excerpt, ""]
    extra = [f"{title} — {url}" for title, url in hits[1:4]]
    if extra:
        lines.append("Other public pages:")
        lines.extend(extra)
    lines.append("Saved in the database.")
    summary = "\n".join(lines).strip()
    save_note(topic, summary, page_url)
    return summary + "\n" + page_url


def _search(topic: str) -> list[tuple[str, str]]:
    body = _fetch(_SEARCH + "?q=" + quote_plus(topic), limit=200_000)
    parser = _LinkParser()
    parser.feed(body.decode("utf-8", errors="replace"))
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for title, href in parser.links:
        url = _result_url(href)
        if not url or url in seen:
            continue
        try:
            _public_url(url)
        except OSError:
            continue
        seen.add(url)
        found.append((title or url, url))
        if len(found) == 4:
            break
    return found


def _read_page(url: str) -> tuple[str, str]:
    if url.lower().split("?", 1)[0].endswith(".pdf"):
        return url, "That result is a PDF. The address is saved so you can fetch the file yourself."
    raw, content_type = _fetch_typed(url, limit=_MAX_BYTES)
    if "pdf" in content_type:
        return url, "That result is a PDF. The address is saved so you can fetch the file yourself."
    if content_type and "html" not in content_type and "text" not in content_type:
        return url, "That page is not a text reference. The address is saved."
    text = _visible_text(raw.decode("utf-8", errors="replace"))
    if len(text) < 40:
        raise OSError("That page had no readable text.")
    return url, text[:_NOTE_CHARS]


def _fetch(url: str, limit: int) -> bytes:
    raw, _kind = _fetch_typed(url, limit)
    return raw


def _fetch_typed(url: str, limit: int) -> tuple[bytes, str]:
    _public_url(url)
    opener = build_opener(_PublicRedirect)
    request = Request(url, headers={"User-Agent": _AGENT, "Accept": "text/html, text/plain"})
    with opener.open(request, timeout=8) as response:
        _public_url(response.geturl())
        kind = str(response.headers.get("Content-Type", "")).lower()
        chunks: list[bytes] = []
        total = 0
        while total < limit:
            piece = response.read(min(65536, limit - total))
            if not piece:
                break
            chunks.append(piece)
            total += len(piece)
    return b"".join(chunks), kind


def _public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise OSError("Only a public web page can be read.")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        raise OSError("That address stays on this PC.")
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError as exc:
        raise OSError(f"Could not reach {host}.") from exc
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue
        if not ip.is_global:
            raise OSError("That address is not a public page.")


def _result_url(href: str) -> str:
    href = href.strip()
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/"):
        href = urljoin(_SEARCH, href)
    parsed = urlparse(href)
    target = parse_qs(parsed.query).get("uddg", [""])[0]
    if target:
        return unquote(target)
    if parsed.scheme in ("http", "https") and "duckduckgo.com" not in (parsed.hostname or ""):
        return href
    return ""


def _visible_text(html: str) -> str:
    parser = _TextParser()
    parser.feed(html)
    return " ".join("".join(parser.parts).split())


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href = ""
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href") or ""
        if href:
            self._href = href
            self._chunks = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            title = " ".join("".join(self._chunks).split())
            if title and title.lower() not in {"next", "previous"}:
                self.links.append((title, self._href))
            self._href = ""
            self._chunks = []


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1
        if tag in {"p", "div", "br", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)
