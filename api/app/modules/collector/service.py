"""C-06 collector: page → visible text split into keyed, hashed sections."""
import hashlib
import json
import re

from selectolax.lexbor import LexborHTMLParser as HTMLParser, LexborNode as Node

LANDMARKS = ("nav", "header", "footer", "aside", "main")
PROMO = re.compile(r"banner|promo|announcement|cookie", re.I)
PRICING = re.compile(r"pricing|plans|price", re.I)


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def normalize(s: str) -> str:
    return " ".join(s.lower().split())


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


def lines(node: Node) -> list[str]:
    return [ln.strip() for ln in node.text(separator="\n").split("\n") if ln.strip()]


def _attrs(node: Node) -> str:
    return f"{node.attributes.get('id') or ''} {node.attributes.get('class') or ''}"


def _inside(node: Node, tags: tuple[str, ...]) -> bool:
    p = node.parent
    while p is not None:
        if p.tag in tags:
            return True
        p = p.parent
    return False


def _promo_parent(node: Node) -> bool:
    p = node.parent
    while p is not None:
        if p.tag != "-text" and PROMO.search(_attrs(p)):
            return True
        p = p.parent
    return False


def _children(node: Node) -> list[Node]:
    return list(node.iter())


def _main_parts(main: Node) -> list[Node]:
    parts = _children(main)
    while len(parts) == 1 and _children(parts[0]):  # unwrap single wrapper divs
        parts = _children(parts[0])
    return parts


def section_nodes(html: str) -> list[tuple[str, str, Node]]:
    """(key base, landmark, node) for each section, in document order. Shared by the extractor."""
    tree = HTMLParser(html)
    tree.strip_tags(["script", "style", "svg", "noscript", "template"])
    body = tree.body
    if body is None:
        return []
    parts: list[tuple[str, str, Node]] = []  # (key base, landmark, node), in document order
    for n in body.traverse():
        if n.tag in LANDMARKS and not _inside(n, LANDMARKS):
            if n.tag != "main":
                parts.append((n.tag, n.tag, n))
                continue
            for p in _main_parts(n):
                h = p.css_first("h1, h2, h3")
                ident = p.attributes.get("id")
                parts.append((f"main#{ident}" if ident else f"main:{slug(h.text()) if h else p.tag}", "main", p))
        elif n.tag != "-text" and PROMO.search(_attrs(n)) and not _inside(n, LANDMARKS) and not _promo_parent(n):
            parts.append(("banner", "banner", n))
    if not any(landmark == "main" for _, landmark, _ in parts):  # no <main>: the whole body is the content
        parts.append(("main:body", "main", body))
    return parts


def is_pricing(node: Node) -> bool:
    return bool(PRICING.search(_attrs(node)) or node.css_first("[id*=pric], [class*=pric], [id*=plan], [class*=plan]"))


def split_sections(html: str) -> tuple[str, list[dict]]:
    """Returns (visible text, sections). Each section: key, landmark, heading, flags, hashes and text offsets."""
    text, sections, seen = "", [], {}
    for base, landmark, node in section_nodes(html):
        ls = lines(node)
        if not ls:
            continue
        seen[base] = seen.get(base, 0) + 1
        key = base if seen[base] == 1 else f"{base}-{seen[base]}"
        raw = "\n".join(ls)
        start = len(text) + (2 if text else 0)
        text = f"{text}\n\n{raw}" if text else raw
        h = node.css_first("h1, h2, h3")
        sections.append({
            "key": key, "landmark": landmark, "heading": h.text(strip=True) if h else None,
            "pricing": is_pricing(node),
            "promo": landmark == "banner", "has_h1": node.css_first("h1") is not None,
            "hash": sha(normalize(raw)), "raw_hash": sha(raw), "html_hash": sha(node.html or ""),
            "start": start, "end": len(text),
        })
    return text, sections


# ---- Fetching (I/O) ---------------------------------------------------------------------------------------------
import gzip  # noqa: E402
import ipaddress  # noqa: E402
import socket  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
from urllib.parse import urljoin, urlsplit  # noqa: E402
from urllib.robotparser import RobotFileParser  # noqa: E402

import httpx  # noqa: E402

from app.config import SUPABASE_SECRET_KEY, SUPABASE_URL, WEB_ORIGIN  # noqa: E402

UA = f"RivalLensBot/0.1 (+{WEB_ORIGIN}/bot)"
MAX_BYTES = 3 * 1024 * 1024
_client = httpx.Client(timeout=15, follow_redirects=False, headers={"User-Agent": UA})
_lock = threading.Lock()
_last_hit: dict[str, float] = {}
_robots: dict[str, tuple[float, RobotFileParser]] = {}


class Blocked(Exception):
    pass


def _guard(url: str) -> str:
    """SSRF guard: http(s) only, and the host must resolve to public addresses."""
    u = urlsplit(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise Blocked("unsupported URL")
    try:
        infos = socket.getaddrinfo(u.hostname, u.port or (443 if u.scheme == "https" else 80))
    except OSError:
        raise Blocked("host does not resolve")
    for info in infos:
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise Blocked("private address")
    return u.hostname


def _polite(host: str) -> None:
    with _lock:  # per-host minimum interval of 1 s
        wait = _last_hit.get(host, 0) + 1 - time.monotonic()
        _last_hit[host] = time.monotonic() + max(wait, 0)
    if wait > 0:
        time.sleep(wait)


def _get(url: str) -> tuple[int, str, str, int]:
    """(status code, content type, decoded text, bytes)."""
    for _ in range(5):  # follow redirects by hand so every hop passes the SSRF guard
        _polite(_guard(url))
        with _client.stream("GET", url) as r:
            if r.is_redirect:
                url = urljoin(url, r.headers["location"])
                continue
            body = b""
            for chunk in r.iter_bytes():
                body += chunk
                if len(body) > MAX_BYTES:
                    raise OverflowError
            return r.status_code, r.headers.get("content-type", ""), body.decode(r.encoding or "utf-8", errors="replace"), len(body)
    raise httpx.TooManyRedirects("too many redirects")


def allowed_by_robots(url: str) -> bool:
    u = urlsplit(url)
    root = f"{u.scheme}://{u.netloc}"
    cached = _robots.get(root)
    if cached is None or time.time() - cached[0] > 24 * 3600:
        rp = RobotFileParser()
        try:
            code, _, body, _ = _get(f"{root}/robots.txt")
            rp.parse(body.splitlines() if code == 200 else [])
        except (httpx.HTTPError, OverflowError):
            rp.parse([])
        cached = _robots[root] = (time.time(), rp)
    return cached[1].can_fetch(UA, url)


def fetch(url: str) -> dict:
    """{status, http_status, html, bytes}; status is one of the C-06 statuses."""
    try:
        if not allowed_by_robots(url):
            return {"status": "blocked_robots", "http_status": None, "html": None, "bytes": 0}
        code, ctype, body, size = _get(url)
    except Blocked:
        return {"status": "failed_http", "http_status": None, "html": None, "bytes": 0}
    except OverflowError:
        return {"status": "too_large", "http_status": None, "html": None, "bytes": MAX_BYTES}
    except httpx.TimeoutException:
        return {"status": "failed_timeout", "http_status": None, "html": None, "bytes": 0}
    except httpx.HTTPError:
        return {"status": "failed_http", "http_status": None, "html": None, "bytes": 0}
    out = {"http_status": code, "html": None, "bytes": size}
    if code != 200 or "text/html" not in ctype:
        return {**out, "status": "failed_http"}
    text, _ = split_sections(body)
    if len(text) < 1024 and size > 50 * 1024:
        return {**out, "status": "needs_js"}
    return {**out, "status": "ok", "html": body}


def fetch_json(url: str) -> dict | None:
    """A public JSON document (a shop's product catalogue), robots.txt respected; None on any failure."""
    try:
        if not allowed_by_robots(url):
            return None
        code, ctype, body, _ = _get(url)
        return json.loads(body) if code == 200 and "json" in ctype else None
    except (Blocked, OverflowError, httpx.HTTPError, ValueError):
        return None


def store_snapshot(source_id: str, observed_at: str, html: str) -> tuple[str, str | None]:
    """Gzips raw HTML into the private 'snapshots' bucket. Returns (sha256, object path or None if upload failed)."""
    digest = sha(html)
    path = f"{source_id}/{observed_at.replace(':', '-')}_{digest[:12]}.html.gz"
    try:
        r = httpx.post(f"{SUPABASE_URL}/storage/v1/object/snapshots/{path}", content=gzip.compress(html.encode()), timeout=20,
                       headers={"apikey": SUPABASE_SECRET_KEY, "Authorization": f"Bearer {SUPABASE_SECRET_KEY}", "Content-Type": "application/gzip"})
        return digest, path if r.status_code in (200, 201) else None
    except httpx.HTTPError:
        return digest, None


def sign_snapshot(path: str, expires_in: int) -> str:
    r = httpx.post(f"{SUPABASE_URL}/storage/v1/object/sign/snapshots/{path}", json={"expiresIn": expires_in}, timeout=15,
                   headers={"apikey": SUPABASE_SECRET_KEY, "Authorization": f"Bearer {SUPABASE_SECRET_KEY}"})
    r.raise_for_status()
    return f"{SUPABASE_URL}/storage/v1{r.json()['signedURL']}"
