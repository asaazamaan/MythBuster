import os
import sys
import json
import time
import re
import datetime
import requests
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.video_downloader_service import VideoDownloaderService
from services.transcription_service import TranscriptionService
from models.video import Video
from databases import get_session

# =============== RAG utilities import ======================
# We keep using the mounted project path (/project) so api can import /project/rag/utils.py
RAG_AVAILABLE = False
rag_utils_path = "/project/rag"
sys.path.append(rag_utils_path)
try:
    from utils import get_chroma_collection, get_source_name_from_url

    RAG_AVAILABLE = True
    print("✅ RAG utilities imported successfully from /project/rag")
except Exception as e:
    print(f"⚠️ RAG utilities not available: {e}")
# ===========================================================


# ----------------- FastAPI plumbing ------------------------
def get_db() -> Session:
    session_gen = get_session()
    return next(session_gen)


router = APIRouter()


# ----------------- Models (request/response) ----------------
class VideoProcessRequest(BaseModel):
    url: str


class VideoProcessResponse(BaseModel):
    success: bool
    message: str
    videoID: Optional[int]
    url: str
    title: Optional[str]
    transcription: Optional[str]
    claims: List[str]
    verdicts: List[
        dict
    ]  # Each element -> verdict for one claim (with unified sources[])
    processed_at: Optional[datetime.datetime]
    from_cache: bool


# ======================== Constants =========================
# Trust allowlist (expand as needed)
TRUSTED_DOMAINS = [
    "who.int",
    "cdc.gov",
    "mayoclinic.org",
    "nih.gov",
    "ncbi.nlm.nih.gov",
    "clevelandclinic.org",
    "webmd.com",
    "diabetes.org",
    "medlineplus.gov",
    "nhs.uk",
    "nature.com",
    "nejm.org",
    "jamanetwork.com",
    "lancet.com",
]
TRUSTED_TLDS = [".gov", ".edu"]

# Caps per plan (≤3 claims total per video)
MAX_CLAIMS = 3
MAX_RAG_SOURCES = 3
MAX_WEB_TRUSTED_SOURCES = 3
MAX_WEB_UNTRUSTED_SOURCES = 2  # stored for transparency; not fed to LLM
SNIPPET_MAX_CHARS = 220  # used ONLY for RAG (not web)

GEMINI_MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
SERPER_SEARCH_URL = "https://google.serper.dev/search"


# ===================== Small helpers ========================
def canonicalize_url(url: str) -> str:
    """Remove tracking params (& similar) for stable dedupe."""
    try:
        p = urlparse(url)
        if not p.scheme:
            return url  # leave odd cases untouched
        # Strip typical tracking params
        qs = [
            (k, v)
            for k, v in parse_qsl(p.query)
            if not k.lower().startswith(("utm_", "gclid", "fbclid"))
        ]
        new_query = urlencode(qs)
        return urlunparse(
            (p.scheme, p.netloc.lower(), p.path, p.params, new_query, "")
        )  # drop fragment
    except Exception:
        return url


def get_domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def is_trusted_url(url: str) -> bool:
    dom = get_domain(url)
    if not dom:
        return False
    # direct match / suffix match
    for td in TRUSTED_DOMAINS:
        if dom == td or dom.endswith(td):
            return True
    # TLD check
    return any(dom.endswith(tld) for tld in TRUSTED_TLDS)


def safe_preview(text: str, limit: int = SNIPPET_MAX_CHARS) -> str:
    """Trim long text (used for RAG only)."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return (text[:limit] + "...") if len(text) > limit else text


def clean_snippet(text: str) -> str:
    """Remove search-engine artifact prefixes like 'المفقودة:' / 'Missing:' and tidy whitespace (WEB ONLY)."""
    if not text:
        return ""
    # Drop lines starting with these markers
    text = re.sub(
        r"^\s*(المفقودة|Missing)\s*:\s*.*$",
        "",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


# =================== LLM-related helpers ====================
def _gemini_post(prompt_text: str, timeout: int = 90) -> Optional[dict]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY missing.")
        return None
    url = f"{GEMINI_MODEL_URL}?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    headers = {"Content-Type": "application/json"}

    # simple retry on overload
    max_retries, delay = 3, 5
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 503 and attempt < max_retries - 1:
                print(
                    f"⚠️ Gemini overloaded (attempt {attempt+1}/{max_retries}); retrying in {delay}s"
                )
                time.sleep(delay)
                delay *= 2
                continue
            else:
                print(f"❌ Gemini error: {resp.status_code} - {resp.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Gemini request error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            return None
    return None


def _extract_text_from_gemini_response(resp_json: dict) -> str:
    try:
        candidates = resp_json.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return ""
        return parts[0].get("text", "").strip()
    except Exception:
        return ""


# ====================== Translation =========================
def translate_to_english(arabic_text: str) -> str:
    """Translate Arabic claim to English for better RAG recall."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return arabic_text
        prompt = (
            "Translate this Arabic medical text to English. "
            "Only return the English translation, no other text:\n\n" + arabic_text
        )
        resp = _gemini_post(prompt, timeout=30)
        if not resp:
            return arabic_text
        translated = _extract_text_from_gemini_response(resp) or arabic_text
        return translated
    except Exception:
        return arabic_text

# =================== Claim extraction =======================

def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` or plain ``` fences if present."""
    if not text:
        return ""
    t = text.strip()
    if t.startswith("```json"):
        t = t[7:]
    elif t.startswith("```"):
        t = t[3:]
    t = t.strip()
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()


def extract_claims_from_transcript(transcript_text: str) -> List[str]:
    """Fallback extractor (Arabic only)."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return []

        prompt = f"""
You are an expert medical claim extractor for an "AI MythBuster" project. Your task is to analyze the provided video transcript to identify and extract factual claims ONLY.

You must follow these rules strictly:

1. The transcript may contain spelling errors, grammar mistakes, and conversational fillers. Ignore these errors and focus on understanding the intended meaning of the text.

2. Read the transcript carefully to determine if the primary topic and claims are related to the medical field of "Diabetes" or diabetic care.

3. If the transcript's claims are NOT about Diabetes, your output MUST be this exact JSON object:
{{"domain_is_diabetes": false, "claims": []}}

4. If the transcript's claims ARE about Diabetes, identify the main claims.

    - Prioritize extracting any claims that are likely to be medically misleading, exaggerated, or incorrect. If no such claims are found, then extract up to three significant factual claims. All claims must be written in correct Arabic, clearly and objectively, while preserving the speaker's original intended meaning without softening or interpreting it.

    - Focus on the single most significant claim if possible.

    - If a single main claim cannot be identified, extract up to a maximum of three distinct, verifiable claims.

    - Each claim should be a concise, objective statement written in Arabic language.

5. Your output MUST be this exact JSON format, with the boolean value and claims array filled in based on the rules above. All claims must be written in Arabic. Do not include any other text, explanations, or conversational language. Return ONLY JSON. Do not wrap the JSON in code fences.

{{
  "domain_is_diabetes": true,
  "claims": [
    "Arabic claim text 1",
    "Arabic claim text 2",
    "Arabic claim text 3"
  ]
}}

Transcript to analyze:
"{transcript_text}"
        """.strip()

        resp = _gemini_post(prompt, timeout=60)
        if not resp:
            return []

        txt = _extract_text_from_gemini_response(resp) or ""
        txt = _strip_code_fences(txt)

        try:
            parsed = json.loads(txt)
        except json.JSONDecodeError:
            # Line-split fallback (keep non-empty lines)
            claims = [line.strip() for line in txt.split("\n") if line.strip()]
            return claims[:MAX_CLAIMS]

        if not parsed.get("domain_is_diabetes", False):
            return []

        claims = [
            c.strip()
            for c in parsed.get("claims", [])
            if isinstance(c, str) and c.strip()
        ]
        return claims[:MAX_CLAIMS]

    except Exception as e:
        print(f"❌ extract_claims_from_transcript error: {e}")
        return []


def extract_claims_with_translation(
    transcript_text: str, max_claims: int = MAX_CLAIMS
) -> List[Dict[str, str]]:
    """
    Primary extractor: returns up to max_claims claims as [{"ar": "...", "en": "..."}].
    Falls back to Arabic-only extractor if parsing fails.
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return []

        prompt = f"""
You are an expert medical claim extractor for an "AI MythBuster" project. Your task is to analyze the provided video transcript to identify and extract factual claims ONLY.

You must follow these rules strictly:
1. The transcript may contain spelling errors, grammar mistakes, and conversational fillers. Ignore these errors and focus on understanding the intended meaning of the text.
2. Read the transcript carefully to determine if the primary topic and claims are related to the medical field of "Diabetes" or diabetic care.
3. If the transcript's claims are NOT about Diabetes, your output MUST be this exact JSON object:
   {{"domain_is_diabetes": false, "claims": []}}

4. If the transcript's claims ARE about Diabetes, identify the main claims.
   - Prioritize extracting any claims that are likely to be medically misleading, exaggerated, or incorrect. If no such claims are found, then extract up to three significant factual claims. All claims must be written in correct Arabic, clearly and objectively, while preserving the speaker's original intended meaning without softening or interpreting it.
   - Focus on the single most significant claim if possible.
   - If a single main claim cannot be identified, extract up to a maximum of three distinct, verifiable claims.
   - Each claim should be a concise, objective statement written in Arabic language in the `ar` field, and you must also provide a precise English translation for that claim in the `en` field. Do not put Arabic text in `en` or English text in `ar`.

5. Your output MUST be this exact JSON format, with the boolean value and claims array filled in based on the rules above. Do not include any other text, explanations, or conversational language. Return ONLY JSON. Do not wrap the JSON in code fences.

{{
  "domain_is_diabetes": true,
  "claims": [
    {{"ar": "Arabic claim text 1", "en": "English translation 1"}},
    {{"ar": "Arabic claim text 2", "en": "English translation 2"}},
    {{"ar": "Arabic claim text 3", "en": "English translation 3"}}
  ]
}}

Transcript to analyze:
"{transcript_text}"
        """.strip()

        resp = _gemini_post(prompt, timeout=60)
        if not resp:
            # Fallback to Arabic-only, then translate
            ar_only = extract_claims_from_transcript(transcript_text)
            return [
                {"ar": ar, "en": translate_to_english(ar)}
                for ar in ar_only[:max_claims]
            ]

        txt = _extract_text_from_gemini_response(resp) or ""
        txt = _strip_code_fences(txt)

        try:
            parsed = json.loads(txt)
        except json.JSONDecodeError:
            # Fallback entirely: Arabic-only → translate
            ar_only = extract_claims_from_transcript(transcript_text)
            return [
                {"ar": ar, "en": translate_to_english(ar)}
                for ar in ar_only[:max_claims]
            ]

        if not parsed.get("domain_is_diabetes", False):
            return []

        out: List[Dict[str, str]] = []
        raw = parsed.get("claims", [])

        for c in raw:
            if isinstance(c, dict):
                ar = (c.get("ar") or "").strip()
                en = (c.get("en") or "").strip()
                if ar and en:
                    out.append({"ar": ar, "en": en})
            elif isinstance(c, str) and c.strip():
                # Model returned plain Arabic strings; translate to EN
                ar = c.strip()
                en = translate_to_english(ar)
                out.append({"ar": ar, "en": en})
            if len(out) >= max_claims:
                break

        return out[:max_claims]

    except Exception as e:
        print(f"❌ extract_claims_with_translation error: {e}")
        return []

# ===================== RAG retrieval ========================
def get_relevant_context(
    claim_ar: str,
    max_results: int = MAX_RAG_SOURCES,
    english_query_override: Optional[str] = None,
) -> List[dict]:
    """Retrieve relevant docs from ChromaDB for the claim (prefers EN query)."""
    if not RAG_AVAILABLE:
        return []
    try:
        english_query = (
            english_query_override or translate_to_english(claim_ar)
        ).strip()
        collection = get_chroma_collection()
        results = collection.query(query_texts=[english_query], n_results=max_results)
        docs_out: List[dict] = []
        if results.get("documents") and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                distance = (
                    results.get("distances", [[1.0]])[0][i]
                    if results.get("distances")
                    else 1.0
                )
                metadata = (
                    results.get("metadatas", [[{}]])[0][i]
                    if results.get("metadatas")
                    else {}
                )
                docs_out.append(
                    {
                        "content": doc,
                        "distance": distance,
                        "relevance_score": max(0.0, 1.0 - float(distance)),
                        "metadata": metadata,
                    }
                )
        return docs_out
    except Exception as e:
        print(f"⚠️ get_relevant_context error: {e}")
        return []


def assemble_rag_sources(
    relevant_docs: List[dict], cap: int = MAX_RAG_SOURCES
) -> List[dict]:
    """Turn RAG docs into uniform source objects with relevance_display bins (uses safe_preview)."""
    out, seen = [], set()
    for idx, d in enumerate(relevant_docs):
        meta = d.get("metadata") or {}
        url = canonicalize_url(meta.get("source_url", "") or meta.get("url", ""))
        if not url or url in seen:
            continue
        seen.add(url)
        # bins by position (already ranked)
        pos = len(out)
        relevance_display = (
            "Most Relevant"
            if pos == 0
            else "Moderately Relevant" if pos == 1 else "Supporting Evidence"
        )
        source_name, source_homepage = get_source_name_from_url(url)
        content = d.get("content") or ""
        out.append(
            {
                "source_type": "rag",
                "trusted": True,
                "source_name": source_name,
                "source_url": url,
                "source_homepage": source_homepage,
                "content_preview": safe_preview(content),  # RAG ONLY trims
                "relevance_display": relevance_display,
            }
        )
        if len(out) >= cap:
            break
    return out


# ===================== Web search ===========================
def web_search_for_claim(
    claim_text: str, lang: str = "ar", num: int = 5
) -> Dict[str, List[dict]]:
    """Return dict with 'trusted' and 'untrusted' lists of web results (title/snippet/url)."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("⚠️ SERPER_API_KEY missing; skipping web search")
        return {"trusted": [], "untrusted": []}

    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": claim_text, "hl": lang, "num": num}
    try:
        r = requests.post(SERPER_SEARCH_URL, headers=headers, json=payload, timeout=20)
        if r.status_code != 200:
            print(f"❌ Serper error: {r.status_code} - {r.text}")
            return {"trusted": [], "untrusted": []}
        organic = (r.json() or {}).get("organic", []) or []

        trusted, untrusted = [], []
        for res in organic[:num]:
            url = canonicalize_url(res.get("link", "") or "")
            if not url:
                continue
            item = {
                "title": res.get("title") or "",
                # WEB: keep raw snippet but clean artifacts; DO NOT truncate
                "snippet": clean_snippet(res.get("snippet") or ""),
                "url": url,
                "domain": get_domain(url),
            }
            (trusted if is_trusted_url(url) else untrusted).append(item)
        return {"trusted": trusted, "untrusted": untrusted}
    except Exception as e:
        print(f"❌ web_search_for_claim error: {e}")
        return {"trusted": [], "untrusted": []}


def assemble_web_sources(
    trusted: List[dict], untrusted: List[dict]
) -> Tuple[List[dict], List[dict]]:
    """
    Convert web results into uniform source objects with relevance_badge.
    IMPORTANT: For WEB we DO NOT truncate. content_preview = cleaned snippet (or title if snippet empty).
    """

    def to_source(res: dict, trusted_flag: bool, pos: int) -> dict:
        source_name, source_homepage = get_source_name_from_url(res.get("url", ""))
        badge = "primary" if trusted_flag else "tertiary"
        cleaned = clean_snippet(res.get("snippet", "") or "")
        content_preview = cleaned if cleaned else (res.get("title") or "")
        return {
            "source_type": "web",
            "trusted": trusted_flag,
            "source_name": source_name,
            "source_url": res.get("url", ""),
            "source_homepage": source_homepage,
            "content_preview": content_preview,  # WEB: cleaned, untruncated
            "relevance_badge": badge,
        }

    # Cap counts
    t_out = [
        to_source(res, True, i)
        for i, res in enumerate(trusted[:MAX_WEB_TRUSTED_SOURCES])
    ]
    u_out = [
        to_source(res, False, i)
        for i, res in enumerate(untrusted[:MAX_WEB_UNTRUSTED_SOURCES])
    ]
    # Dedupe against themselves
    seen = set()
    deduped_t, deduped_u = [], []
    for src in t_out + u_out:
        url = src.get("source_url")
        if url and url not in seen:
            seen.add(url)
            (deduped_t if src["trusted"] else deduped_u).append(src)
    return deduped_t, deduped_u


# ============= Build per-claim context for LLM ==============
def build_context_snippets_for_llm(
    rag_sources: List[dict], web_trusted_sources: List[dict]
) -> List[str]:
    """
    Returns short snippets to feed the LLM.
    - RAG: use content_preview (already safe_preview-trimmed).
    - WEB (trusted only): use cleaned snippet AS-IS (no truncation).
    """
    snippets: List[str] = []
    # RAG snippets
    for s in rag_sources:
        preview = s.get("content_preview") or ""
        if preview:
            snippets.append(preview)
    # WEB trusted snippets
    for s in web_trusted_sources:
        snippet = (
            s.get("content_preview") or ""
        ).strip()  # already cleaned; not truncated
        if snippet:
            snippets.append(snippet)
    # keep it small by source caps only (no per-snippet truncation for web)
    return snippets[: (MAX_RAG_SOURCES + MAX_WEB_TRUSTED_SOURCES)]


# =================== Batch fact-checking ====================
def batch_fact_check_claims_with_sources(
    claims_ar_en: List[dict], contexts: List[dict]
) -> List[dict]:
    """
    claims_ar_en: [{"ar": str, "en": str}, ...]
    contexts: [{
      "rag_sources": [src...],
      "web_trusted_sources": [src...],
      "web_untrusted_sources": [src...],
      "context_texts": [str...]
    }, ...]
    Returns: verdicts[] aligned with input order; we will attach sources afterwards.
    """
    if not claims_ar_en:
        return []

    prompt_header = """
You are an expert medical fact-checker for diabetes claims. Evaluate each claim using the provided CONTEXT_SNIPPETS. These snippets may include medical literature (RAG) and trusted web evidence.

IMPORTANT: Use the relevant medical knowledge provided below to inform your fact-checking. If the provided documents contain information that supports or contradicts the claim, reference this in your reasoning. If context is insufficient, use established medical knowledge.

Verdict definitions:
- TRUE: Medically accurate according to the evidence
- FALSE: Medically incorrect or contradicted by the evidence
- PARTIALLY_TRUE: Contains some truth but is incomplete or misleading based on the evidence
- INSUFFICIENT_INFO: Cannot determine accuracy from the provided evidence

Return ONLY a JSON array of objects in the same order as input, with this exact schema:
{
  "claim": "Arabic claim text",
  "verdict": "TRUE|FALSE|PARTIALLY_TRUE|INSUFFICIENT_INFO",
  "reasoning": "Brief medical explanation in Arabic",
  "medical_category": "treatment|prevention|symptoms|causes|diet|lifestyle"
}
Do not include any other text. Do not wrap the JSON in code fences.

You will now receive a JSON array named CLAIMS.
For each item, use the Arabic claim text (claim_ar) as the "claim" value, and the provided "context_snippets" to inform your judgement.
"""

    claims_block = []
    for i, (c, ctx) in enumerate(zip(claims_ar_en, contexts), start=1):
        snippets = ctx.get("context_texts", [])
        # join short snippets separated by newlines
        ctx_text = "\n\n".join([f"- {s}" for s in snippets]) if snippets else ""
        claims_block.append(
            {
                "id": i,
                "claim_ar": c.get("ar", ""),
                "claim_en": c.get("en", ""),
                "context_snippets": ctx_text,
            }
        )

    # Prompt text with JSON-encoded blocks to reduce formatting mistakes
    prompt = (
        prompt_header
        + "\nCLAIMS:\n"
        + json.dumps(claims_block, ensure_ascii=False, indent=2)
    )

    resp = _gemini_post(prompt, timeout=90)
    if not resp:
        return []

    txt = _extract_text_from_gemini_response(resp) or ""
    txt = _strip_code_fences(txt)  # strip ```json or ``` if present

    try:
        parsed = json.loads(txt)
        if isinstance(parsed, dict):
            parsed = [parsed]
        if not isinstance(parsed, list):
            print("⚠️ Model did not return a JSON array; coercing to list.")
            parsed = [parsed]
        out: List[dict] = []
        for i, item in enumerate(parsed[: len(claims_ar_en)]):
            out.append(
                {
                    "claim": item.get("claim") or claims_ar_en[i]["ar"],
                    "verdict": item.get("verdict", "INSUFFICIENT_INFO"),
                    "reasoning": item.get("reasoning", ""),
                    "medical_category": item.get("medical_category", "treatment"),
                }
            )
        return out
    except json.JSONDecodeError:
        print(f"❌ Failed to parse batch fact-check JSON:\n{txt[:400]}")
        return []

# ===================== Main endpoint ========================
@router.post("/process-video", response_model=VideoProcessResponse)
async def process_video(request: VideoProcessRequest, db: Session = Depends(get_db)):
    """
    Full pipeline:
      - cache check
      - download + transcribe
      - extract up to 3 claims (AR+EN)
      - for each claim: RAG search + web search (trusted/untrusted), normalize sources, build LLM context
      - batch fact-check with per-claim context
      - attach sources (rag + web trusted + web untrusted) to each verdict
      - persist & return
    """
    try:
        print(f"🚀 Processing video: {request.url}")

        # 1) Cache check
        existing = db.query(Video).filter(Video.url == request.url).first()
        if existing:
            print("⚡ Cache hit — returning stored result.")
            return VideoProcessResponse(
                success=True,
                message="Retrieved from cache",
                videoID=existing.videoID,
                url=existing.url,
                title=existing.title,
                transcription=existing.transcription,
                claims=existing.claims or [],
                verdicts=existing.verdicts or [],
                processed_at=existing.processed_at,
                from_cache=True,
            )

        # 2) Download
        dl = VideoDownloaderService()
        dl_res = dl.download_videos([request.url])
        if not dl_res.get("success") or not dl_res.get("downloaded_files"):
            raise HTTPException(status_code=400, detail="Failed to download video")
        audio_file = dl_res["downloaded_files"][0]
        video_title = (
            audio_file.replace(".mp3", "")
            if audio_file.endswith(".mp3")
            else audio_file
        )

        # 3) Transcribe
        transcriber = TranscriptionService()
        tr_res = transcriber.transcribe_audio_files([audio_file])
        if not tr_res.get("transcriptions"):
            raise HTTPException(status_code=500, detail="Failed to transcribe video")
        transcription = tr_res["transcriptions"][0]
        if not transcription.get("success"):
            raise HTTPException(status_code=500, detail="Transcription failed")

        # 4) Extract claims (AR+EN), cap to MAX_CLAIMS
        claims_ar_en: List[dict] = extract_claims_with_translation(
            transcription["transcription"], max_claims=MAX_CLAIMS
        )
        claims_ar = [c["ar"] for c in claims_ar_en][:MAX_CLAIMS]
        print(f"🧩 Extracted {len(claims_ar)} claims")

        verdicts: List[dict] = []
        contexts_for_llm: List[dict] = []
        unified_sources_per_claim: List[List[dict]] = []

        # 5) For each claim: get RAG + Web evidence
        for idx, item in enumerate(claims_ar_en):
            ar = item["ar"]
            en = item["en"]

            # RAG lane
            rag_docs = (
                get_relevant_context(
                    ar, max_results=MAX_RAG_SOURCES, english_query_override=en
                )
                if RAG_AVAILABLE
                else []
            )
            rag_sources = assemble_rag_sources(rag_docs, cap=MAX_RAG_SOURCES)

            # Web lane (Arabic query)
            web_raw = web_search_for_claim(ar, lang="ar", num=5)
            web_trusted, web_untrusted = assemble_web_sources(
                web_raw.get("trusted", []), web_raw.get("untrusted", [])
            )

            # Build snippets to feed the LLM (RAG + trusted web only)
            ctx_snippets = build_context_snippets_for_llm(rag_sources, web_trusted)

            # unify sources for storage/UI: RAG + trusted + untrusted
            unified_sources = []
            # Keep order: RAG → web trusted → web untrusted
            # Dedupe across both lists by URL
            seen = set()
            for bucket in (rag_sources, web_trusted, web_untrusted):
                for s in bucket:
                    u = s.get("source_url")
                    if u and u not in seen:
                        seen.add(u)
                        unified_sources.append(s)

            contexts_for_llm.append(
                {
                    "rag_sources": rag_sources,
                    "web_trusted_sources": web_trusted,
                    "web_untrusted_sources": web_untrusted,
                    "context_texts": ctx_snippets,
                }
            )
            unified_sources_per_claim.append(unified_sources)

        # 6) Batch fact-check with per-claim context blocks
        model_verdicts = batch_fact_check_claims_with_sources(
            claims_ar_en, contexts_for_llm
        )

        # 7) Attach sources to each verdict (aligned by index)
        for i, mv in enumerate(model_verdicts):
            mv["sources"] = (
                unified_sources_per_claim[i]
                if i < len(unified_sources_per_claim)
                else []
            )
            verdicts.append(mv)

        # 8) Persist
        new_video = Video(
            url=request.url,
            title=video_title,
            transcription=transcription.get("transcription"),
            claims=claims_ar,
            verdicts=verdicts,
        )
        db.add(new_video)
        db.commit()
        db.refresh(new_video)

        # Optional: clean processed audio
        try:
            fp = os.path.join("downloads", audio_file)
            if os.path.exists(fp):
                os.remove(fp)
        except Exception as ce:
            print(f"⚠️ Could not delete {audio_file}: {ce}")

        return VideoProcessResponse(
            success=True,
            message="Successfully processed and fact-checked video",
            videoID=new_video.videoID,
            url=new_video.url,
            title=new_video.title,
            transcription=new_video.transcription,
            claims=new_video.claims,
            verdicts=new_video.verdicts,
            processed_at=new_video.processed_at,
            from_cache=False,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ FULL ERROR: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# =================== Utilities endpoints ====================
@router.delete("/clean-downloads")
async def clean_downloads():
    """Delete files in downloads/ via TranscriptionService utility."""
    try:
        transcriber = TranscriptionService()
        return transcriber.cleanup_audio_files()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cached-videos")
async def get_cached_videos(db: Session = Depends(get_db)):
    """List cached videos with counts."""
    try:
        videos = db.query(Video).order_by(Video.processed_at.desc()).all()
        return {
            "success": True,
            "total_videos": len(videos),
            "videos": [
                {
                    "videoID": v.videoID,
                    "url": v.url,
                    "title": v.title,
                    "claims_count": len(v.claims or []),
                    "verdicts_count": len(v.verdicts or []),
                    "processed_at": v.processed_at,
                }
                for v in videos
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
