#!/usr/bin/env python3
import argparse
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

BASE_DIR = Path(__file__).resolve().parent.parent
KB_DIR = BASE_DIR / "knowledge-base"
STORE_DIR = BASE_DIR / "vector-store"
STORE_FILE = STORE_DIR / "memory_index.json"

TOKEN_RE = re.compile(r"[a-zA-Z0-9À-ÿ_-]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text or "") if len(t) > 1]


def read_markdown_docs(root: Path) -> list[dict]:
    docs = []

    for path in sorted(root.rglob("*.md")):
        post = frontmatter.load(path)
        meta = dict(post.metadata)
        content = post.content.strip()

        if not meta:
            continue

        doc_id = meta.get("id")
        if not doc_id:
            continue

        title = meta.get("title", path.stem)
        doc_type = meta.get("type", "unknown")
        tags = meta.get("tags", [])
        universe = meta.get("universe", "unknown")
        summary = meta.get("summary", "")
        status = meta.get("status", "unknown")
        version = meta.get("version", "0.0.0")
        updated_at = meta.get("updated_at", "")

        if isinstance(tags, str):
            tags = [tags]

        searchable_parts = [
            title,
            doc_type,
            universe,
            summary,
            status,
            version,
            " ".join(tags),
            content,
        ]
        searchable_text = "\
".join(searchable_parts).strip()
        tokens = tokenize(searchable_text)

        docs.append(
            {
                "id": doc_id,
                "title": title,
                "type": doc_type,
                "tags": tags,
                "universe": universe,
                "summary": summary,
                "status": status,
                "version": version,
                "updated_at": updated_at,
                "path": str(path.relative_to(BASE_DIR)),
                "content": content,
                "tokens": tokens,
                "token_count": len(tokens),
            }
        )

    return docs


def build_inverted_index(docs: list[dict]) -> dict:
    inverted = defaultdict(dict)
    doc_freq = Counter()
    avg_doc_len = 0.0

    for doc in docs:
        counts = Counter(doc["tokens"])
        for term, tf in counts.items():
            inverted[term][doc["id"]] = tf
        for term in counts:
            doc_freq[term] += 1

    if docs:
        avg_doc_len = sum(doc["token_count"] for doc in docs) / len(docs)

    store_docs = {}
    for doc in docs:
        store_docs[doc["id"]] = {
            "id": doc["id"],
            "title": doc["title"],
            "type": doc["type"],
            "tags": doc["tags"],
            "universe": doc["universe"],
            "summary": doc["summary"],
            "status": doc["status"],
            "version": doc["version"],
            "updated_at": doc["updated_at"],
            "path": doc["path"],
            "content": doc["content"],
            "token_count": doc["token_count"],
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "doc_count": len(docs),
        "avg_doc_len": avg_doc_len,
        "doc_freq": dict(doc_freq),
        "inverted_index": {term: postings for term, postings in inverted.items()},
        "documents": store_docs,
    }


def score_bm25_like(query_terms: list[str], store: dict, top_k: int = 10) -> list[dict]:
    k1 = 1.5
    b = 0.75
    total_docs = store.get("doc_count", 0) or 1
    avgdl = store.get("avg_doc_len", 0.0) or 1.0
    doc_freq = store.get("doc_freq", {})
    inverted = store.get("inverted_index", {})
    documents = store.get("documents", {})

    scores = defaultdict(float)

    for term in query_terms:
        postings = inverted.get(term, {})
        if not postings:
            continue

        df = doc_freq.get(term, 0)
        idf = math.log(1 + ((total_docs - df + 0.5) / (df + 0.5)))

        for doc_id, tf in postings.items():
            doc = documents.get(doc_id)
            if not doc:
                continue
            dl = doc.get("token_count", 0) or 1
            denom = tf + k1 * (1 - b + b * (dl / avgdl))
            scores[doc_id] += idf * ((tf * (k1 + 1)) / denom)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
    results = []

    for doc_id, score in ranked:
        doc = documents[doc_id]
        results.append(
            {
                "id": doc["id"],
                "title": doc["title"],
                "type": doc["type"],
                "summary": doc["summary"],
                "tags": doc["tags"],
                "universe": doc["universe"],
                "path": doc["path"],
                "score": round(score, 6),
            }
        )

    return results


def save_store(store: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(store, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )


def load_store(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_index() -> int:
    docs = read_markdown_docs(KB_DIR)
    if not docs:
        raise SystemExit(
            "Aucun document Markdown avec frontmatter valide trouvé dans knowledge-base/"
        )
    store = build_inverted_index(docs)
    save_store(store, STORE_FILE)
    print(f"Index créé: {STORE_FILE}")
    print(f"Documents indexés: {store['doc_count']}")
    return 0


def cmd_search(query: str, top_k: int) -> int:
    if not STORE_FILE.exists():
        raise SystemExit(
            "Index absent. Lance d'abord: python pipelines/index_rag.py index"
        )
    store = load_store(STORE_FILE)
    terms = tokenize(query)
    results = score_bm25_like(terms, store, top_k=top_k)
    print(
        json.dumps({"query": query, "results": results}, ensure_ascii=False, indent=2)
    )
    return 0


def main():
    parser = argparse.ArgumentParser(description="MEM indexer and search tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("index", help="Indexer la knowledge base")

    search_parser = subparsers.add_parser("search", help="Rechercher dans l'index")
    search_parser.add_argument("query", type=str, help="Texte de recherche")
    search_parser.add_argument("--top-k", type=int, default=5)

    args = parser.parse_args()

    if args.command == "index":
        return cmd_index()
    if args.command == "search":
        return cmd_search(args.query, args.top_k)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
