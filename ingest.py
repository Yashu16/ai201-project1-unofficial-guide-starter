from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup

from config import (
    ARTIFACTS_PATH,
    DOCUMENTS_PATH,
    MAX_REDDIT_THREADS_PER_SEARCH,
    MAX_WEB_TEXT_CHARS,
    RAW_DOCUMENTS_PATH,
    REQUEST_TIMEOUT_SECONDS,
    SOURCES,
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


@dataclass
class IngestionStatus:
    source_id: str
    source_name: str
    url: str
    status: str
    note: str
# Describes outcome of ingesting one source

def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _ensure_dirs() -> None:
    DOCUMENTS_PATH.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_PATH.mkdir(parents=True, exist_ok=True)


def _load_local_documents() -> List[Dict]:
    docs: List[Dict] = []

    if not DOCUMENTS_PATH.exists():
        return docs

    supported = {".txt", ".md", ".html", ".json"}
    for path in sorted(DOCUMENTS_PATH.iterdir()):
        if path.is_dir() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in supported:
            continue

        text = _read_local_file(path)
        if not text:
            continue

        docs.append(
            {
                "doc_id": f"local:{path.stem}",
                "title": path.stem,
                "source": "local_documents",
                "source_kind": "local",
                "url": str(path),
                "text": clean_text(text),
                "metadata": {"filename": path.name, "extension": path.suffix.lower()},
            }
        )

    return docs


def _read_local_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".html"}:
        return path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".json":
        raw = path.read_text(encoding="utf-8", errors="ignore")
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        return json.dumps(obj, ensure_ascii=True)

    return ""


def _fetch(url: str) -> requests.Response:
    headers = {"User-Agent": USER_AGENT}
    return requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)


def _extract_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "footer", "nav"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return clean_text("\n".join(lines))


def _old_reddit_url(url: str) -> str:
    return url.replace("https://www.reddit.com", "https://old.reddit.com")


def _extract_reddit_thread_links(search_html: str) -> List[str]:
    soup = BeautifulSoup(search_html, "html.parser")
    links = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if "/comments/" not in href:
            continue

        if href.startswith("/"):
            href = f"https://old.reddit.com{href}"
        elif href.startswith("https://www.reddit.com"):
            href = href.replace("https://www.reddit.com", "https://old.reddit.com")

        if href not in links:
            links.append(href)

        if len(links) >= MAX_REDDIT_THREADS_PER_SEARCH:
            break

    return links


def _extract_reddit_thread_text(thread_html: str) -> str:
    soup = BeautifulSoup(thread_html, "html.parser")

    blocks: List[str] = []

    title = soup.find("a", class_="title")
    if title and title.get_text(strip=True):
        blocks.append(f"Title: {title.get_text(strip=True)}")

    for comment in soup.select("div.md"):
        text = comment.get_text(" ", strip=True)
        if text:
            blocks.append(text)

    return clean_text("\n".join(blocks))


def _ingest_reddit_search_source(source: Dict) -> Tuple[List[Dict], IngestionStatus]:
    url = _old_reddit_url(source["url"])

    try:
        response = _fetch(url)
    except Exception as exc:
        return [], IngestionStatus(source["id"], source["name"], source["url"], "failed", str(exc))

    if response.status_code >= 400:
        return [], IngestionStatus(
            source["id"],
            source["name"],
            source["url"],
            "failed",
            f"HTTP {response.status_code} while fetching search page.",
        )

    links = _extract_reddit_thread_links(response.text)
    if not links:
        return [], IngestionStatus(
            source["id"],
            source["name"],
            source["url"],
            "skipped",
            "No thread links found from search page. Reddit may require auth or changed markup.",
        )

    docs: List[Dict] = []
    for i, link in enumerate(links):
        try:
            thread_response = _fetch(link)
            if thread_response.status_code >= 400:
                continue
        except Exception:
            continue

        text = _extract_reddit_thread_text(thread_response.text)
        if not text:
            continue

        # Drop threads that aren't about UMD academics.
        text_lower = text.lower()
        _RELEVANT_KEYWORDS = {"cmsc", "class", "course", "professor", "prof", "grade", "exam", "lecture", "umd", "terp"}
        if "umd" not in text_lower and "terp" not in text_lower:
            continue
        if text_lower.count("umbc") > text_lower.count("umd"):
            continue
        if sum(1 for kw in _RELEVANT_KEYWORDS if kw in text_lower) < 3:
            continue

        docs.append(
            {
                "doc_id": f"{source['id']}:{i}",
                "title": f"{source['name']} thread {i + 1}",
                "source": source["name"],
                "source_kind": source["source_kind"],
                "url": link,
                "text": text[:MAX_WEB_TEXT_CHARS],
                "metadata": {"origin_search_url": source["url"]},
            }
        )

    if not docs:
        return [], IngestionStatus(
            source["id"],
            source["name"],
            source["url"],
            "skipped",
            "Search was fetched but no usable thread content was extracted.",
        )

    return docs, IngestionStatus(
        source["id"],
        source["name"],
        source["url"],
        "ok",
        f"Extracted {len(docs)} thread documents from search results.",
    )


def _ingest_generic_web_source(source: Dict) -> Tuple[List[Dict], IngestionStatus]:
    try:
        response = _fetch(source["url"])
    except Exception as exc:
        return [], IngestionStatus(source["id"], source["name"], source["url"], "failed", str(exc))

    if response.status_code >= 400:
        return [], IngestionStatus(
            source["id"],
            source["name"],
            source["url"],
            "failed",
            f"HTTP {response.status_code}.",
        )

    text = _extract_html_text(response.text)
    if not text:
        return [], IngestionStatus(
            source["id"],
            source["name"],
            source["url"],
            "skipped",
            "Page fetched but extracted text was empty.",
        )

    doc = {
        "doc_id": source["id"],
        "title": source["name"],
        "source": source["name"],
        "source_kind": source["source_kind"],
        "url": source["url"],
        "text": text[:MAX_WEB_TEXT_CHARS],
        "metadata": {},
    }
    return [doc], IngestionStatus(source["id"], source["name"], source["url"], "ok", "Extracted page text.")


def _ingest_planetterp_api_source(source: Dict) -> Tuple[List[Dict], IngestionStatus]:
    try:
        response = _fetch(source["url"])
    except Exception as exc:
        return [], IngestionStatus(source["id"], source["name"], source["url"], "failed", str(exc))

    if response.status_code >= 400:
        return [], IngestionStatus(
            source["id"], source["name"], source["url"], "failed", f"HTTP {response.status_code}."
        )

    try:
        items = response.json()
    except Exception as exc:
        return [], IngestionStatus(source["id"], source["name"], source["url"], "failed", f"JSON parse error: {exc}")

    docs: List[Dict] = []
    for item in items:
        reviews = item.get("reviews") or []
        for j, rev in enumerate(reviews):
            review_text = (rev.get("review") or "").strip()
            if not review_text:
                continue

            professor = rev.get("professor", "")
            course = rev.get("course") or item.get("name", "")
            rating = rev.get("rating")
            expected_grade = rev.get("expected_grade", "")

            text = f"Course: {course}. Professor: {professor}. Rating: {rating}/5. Expected grade: {expected_grade}. Review: {review_text}"

            docs.append(
                {
                    "doc_id": f"{source['id']}:{course}:{j}",
                    "title": f"{course} - {professor}",
                    "source": source["name"],
                    "source_kind": source["source_kind"],
                    "url": f"https://planetterp.com/course/{course}",
                    "text": clean_text(text),
                    "metadata": {"professor": professor, "course": course, "rating": rating},
                }
            )

    if not docs:
        return [], IngestionStatus(
            source["id"], source["name"], source["url"], "skipped", "No reviews found in API response."
        )

    return docs, IngestionStatus(
        source["id"], source["name"], source["url"], "ok", f"Extracted {len(docs)} reviews."
    )


def ingest_sources(include_web: bool = True) -> Tuple[List[Dict], List[IngestionStatus]]:
    _ensure_dirs()

    documents = _load_local_documents()
    status_rows: List[IngestionStatus] = [
        IngestionStatus(
            source_id="local_documents",
            source_name="Local documents/ files",
            url=str(DOCUMENTS_PATH),
            status="ok" if documents else "skipped",
            note=f"Loaded {len(documents)} local file(s).",
        )
    ]

    if not include_web:
        return documents, status_rows

    for source in SOURCES:
        source_url = source["url"].lower()

        if "reddit.com" in source_url and "/search/" in source_url:
            docs, status = _ingest_reddit_search_source(source)
        elif "planetterp.com/api" in source_url:
            docs, status = _ingest_planetterp_api_source(source)
        else:
            docs, status = _ingest_generic_web_source(source)

        documents.extend(docs)
        status_rows.append(status)

    return documents, status_rows


def save_raw_documents(documents: List[Dict], output_path: Path = RAW_DOCUMENTS_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        for doc in documents:
            f.write(json.dumps(doc, ensure_ascii=True) + "\n")

    return output_path


def run_ingestion(include_web: bool = True) -> Tuple[List[Dict], List[IngestionStatus], Path]:
    docs, status_rows = ingest_sources(include_web=include_web)
    raw_path = save_raw_documents(docs)
    return docs, status_rows, raw_path


def _print_status_table(status_rows: List[IngestionStatus]) -> None:
    print("\nIngestion status:")
    print("-" * 95)
    print(f"{'source_id':<28} {'status':<10} {'url':<45} note")
    print("-" * 95)
    for row in status_rows:
        compact_url = row.url if len(row.url) <= 45 else row.url[:42] + "..."
        print(f"{row.source_id:<28} {row.status:<10} {compact_url:<45} {row.note}")
    print("-" * 95)


if __name__ == "__main__":
    docs, statuses, output_file = run_ingestion(include_web=True)
    print(f"Saved {len(docs)} raw document(s) to: {output_file}")
    _print_status_table(statuses)
