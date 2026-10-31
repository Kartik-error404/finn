"""Start FINN:  python run.py   (then open http://localhost:8000 on your phone/laptop)"""
import os
import sys


def load_dotenv(path=".env"):
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from finn.server import serve  # noqa: E402  (import after env is loaded)

if __name__ == "__main__":
    serve(port=int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8000)))
