"""Zero-dependency HTTP server: JSON API + static mobile web app."""
import json
import mimetypes
import os
import re
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import llm, pull, push, sample
from .config import MODE, RESEARCH_SUGGESTIONS, WEB_DIR, load_portfolio, load_settings, save_portfolio, save_settings

SYM_RX = re.compile(r"^[A-Z0-9&\-]{1,20}$")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[http]", self.command, self.path, args[1] if len(args) > 1 else "")

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def _symbol(self, q):
        s = (q.get("symbol") or [""])[0].upper().strip().replace(".NS", "").replace(".BO", "")
        if not SYM_RX.match(s):
            raise ValueError("bad symbol")
        return s

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        try:
            if u.path == "/api/meta":
                return self._send(200, {
                    "portfolio": load_portfolio(),
                    "suggestions": RESEARCH_SUGGESTIONS,
                    "mode": MODE,
                    "llm": llm.enabled(),
                    "llm_stats": llm.STATS,
                    "settings": load_settings(),
                })
            if u.path == "/api/digest":
                hours = max(1, min(24 * 30, int((q.get("hours") or ["24"])[0])))
                return self._send(200, push.digest(hours))
            if u.path == "/api/alerts":
                return self._send(200, push.alerts())
            if u.path == "/api/research":
                return self._send(200, pull.research(self._symbol(q)))
            return self._static(u.path)
        except ValueError as e:
            return self._send(400, {"error": str(e)})
        except Exception as e:
            traceback.print_exc()
            return self._send(500, {"error": f"{e.__class__.__name__}: {e}"})

    def do_POST(self):
        u = urlparse(self.path)
        try:
            body = self._body()
            if u.path == "/api/settings":
                return self._send(200, save_settings(body))
            if u.path == "/api/portfolio":
                action = body.get("action")
                port = load_portfolio()
                if action == "add":
                    sym = self._symbol({"symbol": [body.get("symbol", "")]})
                    if not any(p["symbol"] == sym for p in port):
                        prof = sample.COMPANY_PROFILES.get(sym, {})
                        port.append({
                            "symbol": sym,
                            "name": body.get("name") or prof.get("name") or f"{sym.title()} Ltd",
                            "sector": body.get("sector") or prof.get("sector") or "NSE Listed",
                        })
                        save_portfolio(port)
                elif action == "remove":
                    sym = self._symbol({"symbol": [body.get("symbol", "")]})
                    port = [p for p in port if p["symbol"] != sym]
                    save_portfolio(port)
                elif action == "reset":
                    from .config import PORTFOLIO
                    port = save_portfolio(list(PORTFOLIO))
                return self._send(200, {"portfolio": port})
            if u.path == "/api/ask":
                sym = self._symbol({"symbol": [body.get("symbol", "")]})
                return self._send(200, pull.ask(sym, str(body.get("question", ""))[:500]))
            return self._send(404, {"error": "not found"})
        except Exception as e:
            traceback.print_exc()
            return self._send(500, {"error": str(e)})

    def _static(self, path):
        path = "/index.html" if path in ("", "/") else path
        full = os.path.realpath(os.path.join(WEB_DIR, path.lstrip("/")))
        if not full.startswith(os.path.realpath(WEB_DIR)) or not os.path.isfile(full):
            return self._send(404, {"error": "not found"})
        with open(full, "rb") as f:
            self._send(200, f.read(), mimetypes.guess_type(full)[0] or "application/octet-stream")


def serve(host="0.0.0.0", port=8000):
    print(f"FINN running on http://localhost:{port}  (mode={MODE}, llm={'on' if llm.enabled() else 'off'})")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
