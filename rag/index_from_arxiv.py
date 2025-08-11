import arxiv
from uuid import uuid4
from typing import List
import io
import requests
from pdfminer.high_level import extract_text as pdf_extract_text

# Reuse existing embedder and Chroma collection from your RAG utilities
from utils import get_embedder, get_chroma_collection


def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 250) -> List[str]:
    """Simple text chunker for abstracts/full text."""
    if not text:
        return []
    text = text.strip()
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def extract_pdf_text(pdf_url: str, timeout: int = 60) -> str:
    """Download a PDF and extract text. Returns empty string on failure."""
    if not pdf_url:
        return ""
    try:
        resp = requests.get(pdf_url, timeout=timeout)
        if resp.status_code != 200 or not resp.content:
            return ""
        with io.BytesIO(resp.content) as f:
            text = pdf_extract_text(f) or ""
            return text
    except Exception as e:
        print(f"⚠️ PDF extract failed: {e}")
        return ""


def index_arxiv(query: str = "diabetes", max_results: int = 150, prefer_pdf: bool = True):
    """Index arXiv titles+abstracts or full PDFs into the SAME Chroma collection.
    prefer_pdf: if True, try full text from the PDF first, else fall back to title+abstract.
    """
    embedder = get_embedder()
    collection = get_chroma_collection()

    client = arxiv.Client(page_size=50, delay_seconds=3, num_retries=2)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    total_chunks = 0
    batch_docs: List[str] = []
    batch_embs: List[List[float]] = []
    batch_ids: List[str] = []
    batch_meta: List[dict] = []

    def flush_batch():
        nonlocal batch_docs, batch_embs, batch_ids, batch_meta
        if not batch_docs:
            return
        collection.add(
            documents=batch_docs,
            embeddings=batch_embs,
            ids=batch_ids,
            metadatas=batch_meta,
        )
        print(f"✅ Added batch of {len(batch_docs)} chunks to Chroma")
        batch_docs, batch_embs, batch_ids, batch_meta = [], [], [], []

    for i, paper in enumerate(client.results(search), start=1):
        try:
            title = (paper.title or "").strip()
            summary = (paper.summary or "").strip()
            source_url = paper.entry_id  # e.g., https://arxiv.org/abs/xxxx.xxxxx
            pdf_url = getattr(paper, 'pdf_url', None)

            text = ""
            content_scope = "abstract"
            if prefer_pdf and pdf_url:
                text = extract_pdf_text(pdf_url)
                if text.strip():
                    content_scope = "full_text"
                else:
                    # Fallback to title+abstract
                    text = f"{title}\n\n{summary}".strip()
                    content_scope = "abstract"
            else:
                text = f"{title}\n\n{summary}".strip()
                content_scope = "abstract"

            if not text:
                continue

            chunks = chunk_text(text)
            if not chunks:
                continue

            embeddings = embedder.encode(chunks).tolist()
            ids = [str(uuid4()) for _ in chunks]
            meta = [
                {
                    "source_url": source_url,
                    "source_pdf_url": pdf_url,
                    "source": "arxiv",
                    "arxiv_id": paper.get_short_id() if hasattr(paper, 'get_short_id') else source_url.rsplit('/', 1)[-1],
                    "title": title,
                    "published": paper.published.isoformat() if paper.published else None,
                    "content_scope": content_scope,
                }
                for _ in chunks
            ]

            batch_docs.extend(chunks)
            batch_embs.extend(embeddings)
            batch_ids.extend(ids)
            batch_meta.extend(meta)
            total_chunks += len(chunks)

            print(f"📄 [{i}] {title[:80]}... → {len(chunks)} chunks ({content_scope})")

            # Flush every ~500 chunks to keep memory low
            if len(batch_docs) >= 500:
                flush_batch()
        except Exception as e:
            print(f"❌ Error on paper {i}: {e}")
            continue

    # Final flush
    flush_batch()
    print(f"🎉 Done. Indexed ~{total_chunks} chunks from arXiv query: '{query}' (prefer_pdf={prefer_pdf})")


if __name__ == "__main__":
    print("🔎 Indexing arXiv papers into the existing Chroma collection (equal weight)...")
    index_arxiv(query="diabetes", max_results=150, prefer_pdf=True)
