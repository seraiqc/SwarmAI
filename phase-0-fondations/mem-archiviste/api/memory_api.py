#!/usr/bin/env python3
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
STORE_FILE = BASE_DIR / "vector-store" / "memory_index.json"
PIPELINE_DIR = BASE_DIR / "pipelines"

if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from index_rag import load_store, score_bm25_like, tokenize  # noqa: E402

CACHE_MODULE_DIR = BASE_DIR / "cache"
if str(CACHE_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(CACHE_MODULE_DIR))

from query_cache import clear_expired_cache, get_cached_search, set_cached_search  # noqa: E402


HOST = "127.0.0.1"
PORT = 8131


def ensure_store():
    if not STORE_FILE.exists():
        raise FileNotFoundError(
            "Index absent. Lance d'abord: python pipelines/index_rag.py index"
        )
    return load_store(STORE_FILE)


class MemoryHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self._send_json({"status": "ok", "service": "mem-api"})
            return

        if parsed.path == "/search":
            try:
                store = ensure_store()
            except FileNotFoundError as e:
                self._send_json({"error": str(e)}, status=400)
                return

            params = parse_qs(parsed.query)
            query = params.get("q", [""])[0].strip()
            top_k_raw = params.get("top_k", ["5"])[0]

            if not query:
                self._send_json({"error": "Paramètre q requis"}, status=400)
                return

            try:
                top_k = max(1, min(int(top_k_raw), 20))
            except ValueError:
                top_k = 5

            clear_expired_cache(ttl_seconds=3600)

            cached = get_cached_search(query, top_k, ttl_seconds=3600)
            if cached is not None:
                cached["cache"] = "hit"
                self._send_json(cached)
                return

            terms = tokenize(query)
            results = score_bm25_like(terms, store, top_k=top_k)

            payload = {
                "query": query,
                "top_k": top_k,
                "count": len(results),
                "results": results,
                "cache": "miss",
            }

            set_cached_search(query, top_k, payload)
            self._send_json(payload)
            return

        if parsed.path == "/document":
            try:
                store = ensure_store()
            except FileNotFoundError as e:
                self._send_json({"error": str(e)}, status=400)
                return

            params = parse_qs(parsed.query)
            doc_id = params.get("id", [""])[0].strip()

            if not doc_id:
                self._send_json({"error": "Paramètre id requis"}, status=400)
                return

            doc = store.get("documents", {}).get(doc_id)
            if not doc:
                self._send_json({"error": "Document introuvable"}, status=404)
                return

            self._send_json({"document": doc})
            return

        if parsed.path == "/documents":
            try:
                store = ensure_store()
            except FileNotFoundError as e:
                self._send_json({"error": str(e)}, status=400)
                return

            docs = list(store.get("documents", {}).values())
            docs = sorted(docs, key=lambda d: d["id"])
            self._send_json({"count": len(docs), "documents": docs})
            return

        self._send_json({"error": "Route introuvable"}, status=404)

    def log_message(self, format, *args):
        return


def main():
    server = HTTPServer((HOST, PORT), MemoryHandler)
    print(f"MEM API active sur http://{HOST}:{PORT}")
    print("Routes: /health /search?q=... /document?id=... /documents")
    server.serve_forever()


if __name__ == "__main__":
    main()
