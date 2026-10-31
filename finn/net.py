"""Tiny HTTP layer: urllib + cookie jar + on-disk TTL cache. No third-party deps."""
import gzip
import hashlib
import http.cookiejar
import json
import os
import time
import urllib.request

from .config import CACHE_DIR

UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36")

_jar = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_jar))


def _cache_path(key):
    h = hashlib.sha1(key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, "http", h[:2], h)


def cache_get(key, ttl):
    p = _cache_path(key)
    try:
        if time.time() - os.path.getmtime(p) < ttl:
            with open(p, "rb") as f:
                return f.read()
    except OSError:
        pass
    return None


def cache_put(key, data: bytes):
    p = _cache_path(key)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data)


def fetch(url, ttl=3600, headers=None, timeout=15) -> bytes:
    """GET with caching. Raises on network failure (callers fall back to demo data)."""
    cached = cache_get(url, ttl)
    if cached is not None:
        return cached
    h = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9",
         "Accept-Encoding": "gzip"}
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    with _opener.open(req, timeout=timeout) as r:
        data = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
    cache_put(url, data)
    return data


def fetch_json(url, ttl=3600, headers=None):
    return json.loads(fetch(url, ttl, headers).decode("utf-8", "replace"))


def warm_cookies(url):
    """Some sites (NSE) need a homepage hit to set cookies before the API works."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        _opener.open(req, timeout=10).read()
    except Exception:
        pass
