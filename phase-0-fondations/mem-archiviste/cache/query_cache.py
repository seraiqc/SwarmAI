#!/usr/bin/env python3
import hashlib
import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache" / "search"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(query: str, top_k: int) -> str:
    raw = f"{query.strip().lower()}::{top_k}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def get_cached_search(query: str, top_k: int, ttl_seconds: int = 3600):
    key = _cache_key(query, top_k)
    path = _cache_path(key)

    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    created_at = payload.get("created_at", 0)
    if time.time() - created_at > ttl_seconds:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return None

    return payload.get("data")


def set_cached_search(query: str, top_k: int, data: dict):
    key = _cache_key(query, top_k)
    path = _cache_path(key)

    payload = {
        "created_at": time.time(),
        "query": query,
        "top_k": top_k,
        "data": data,
    }

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def clear_expired_cache(ttl_seconds: int = 3600):
    now = time.time()

    for path in CACHE_DIR.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            created_at = payload.get("created_at", 0)
            if now - created_at > ttl_seconds:
                path.unlink()
        except Exception:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
