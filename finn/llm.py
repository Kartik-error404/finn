"""Model router with response cache.

Any OpenAI-compatible endpoint works (Groq, Gemini's OpenAI endpoint, OpenRouter, Ollama).
- cheap model  -> bulk work: classifying ambiguous filings, one-line summaries, field extraction
- strong model -> reasoning: promise-vs-delivered, bull/bear, grounded Q&A
Every call is cached on disk by (model, prompt) so re-runs cost nothing.
If no key is configured, callers fall back to deterministic rules.
"""
import hashlib
import json
import os
import urllib.request

from .config import CACHE_DIR

BASE_URL = os.environ.get("FINN_LLM_BASE_URL", "https://api.groq.com/openai/v1")
API_KEY = os.environ.get("FINN_LLM_API_KEY", "")
CHEAP = os.environ.get("FINN_CHEAP_MODEL", "llama-3.1-8b-instant")
STRONG = os.environ.get("FINN_STRONG_MODEL", "llama-3.3-70b-versatile")

STATS = {"calls": 0, "cache_hits": 0, "prompt_chars": 0}


def enabled():
    return bool(API_KEY) or "localhost" in BASE_URL or "127.0.0.1" in BASE_URL


def _path(key):
    return os.path.join(CACHE_DIR, "llm", hashlib.sha1(key.encode()).hexdigest() + ".json")


def complete(prompt, tier="cheap", system=None, max_tokens=600, as_json=False):
    """Return model text (or parsed JSON). Returns None if LLM is unavailable or fails."""
    if not enabled():
        return None
    model = STRONG if tier == "strong" else CHEAP
    key = json.dumps([model, system, prompt, as_json])
    p = _path(key)
    if os.path.exists(p):
        STATS["cache_hits"] += 1
        with open(p) as f:
            out = json.load(f)["out"]
    else:
        msgs = ([{"role": "system", "content": system}] if system else []) + \
               [{"role": "user", "content": prompt}]
        body = {"model": model, "messages": msgs, "temperature": 0.1, "max_tokens": max_tokens}
        if as_json:
            body["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(
            BASE_URL.rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.load(r)["choices"][0]["message"]["content"]
        except Exception as e:  # network / quota / bad model -> graceful fallback
            print(f"[llm] {model} failed: {e}")
            return None
        STATS["calls"] += 1
        STATS["prompt_chars"] += len(prompt)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            json.dump({"model": model, "out": out}, f)
    if as_json:
        try:
            return json.loads(out[out.find("{"): out.rfind("}") + 1])
        except ValueError:
            return None
    return out.strip()
