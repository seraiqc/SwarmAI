import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_SCRIPT = BASE_DIR / "pipelines" / "index_rag.py"
STORE_FILE = BASE_DIR / "vector-store" / "memory_index.json"


def run_cmd(*args):
    return subprocess.run(
        [sys.executable, str(INDEX_SCRIPT), *args],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=True,
    )


def parse_search_output(stdout: str) -> dict:
    return json.loads(stdout)


def test_index_builds_store():
    run_cmd("index")
    assert STORE_FILE.exists(), "Le fichier memory_index.json doit être créé"

    data = json.loads(STORE_FILE.read_text(encoding="utf-8"))
    assert data["doc_count"] >= 5
    assert "char-kael" in data["documents"]
    assert "char-maera" in data["documents"]


def test_search_returns_kael_or_archives():
    run_cmd("index")
    result = run_cmd("search", "Kael archives Nord", "--top-k", "5")
    payload = parse_search_output(result.stdout)

    ids = [item["id"] for item in payload["results"]]
    assert "char-kael" in ids or "theme-archives-perdues" in ids


def test_search_returns_maera():
    run_cmd("index")
    result = run_cmd("search", "pactes anciens archiviste", "--top-k", "5")
    payload = parse_search_output(result.stdout)

    ids = [item["id"] for item in payload["results"]]
    assert "char-maera" in ids


def test_search_returns_citadelle():
    run_cmd("index")
    result = run_cmd("search", "forteresse routes nord", "--top-k", "5")
    payload = parse_search_output(result.stdout)

    ids = [item["id"] for item in payload["results"]]
    assert "loc-citadelle-noire" in ids


def test_search_output_has_scores():
    run_cmd("index")
    result = run_cmd("search", "archives pouvoir royaume", "--top-k", "5")
    payload = parse_search_output(result.stdout)

    assert "results" in payload
    assert isinstance(payload["results"], list)

    if payload["results"]:
        first = payload["results"][0]
        assert "id" in first
        assert "title" in first
        assert "score" in first
        assert isinstance(first["score"], float)
