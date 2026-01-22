# MythBuster: Automated Fact-Checking for Arabic Videos About Diabetes

🔗 **Demo page:** https://asaazamaan.github.io/mythbuster-demo/  
🎥 **Demo video:** https://www.youtube.com/watch?v=p8ZqCEGbmfs  

**MythBuster** is an end-to-end system that automatically fact-checks diabetes-related medical claims in short Arabic videos.

Given a video URL, the system transcribes spoken Arabic, extracts check-worthy medical claims, retrieves supporting evidence, and produces **evidence-grounded Arabic verdicts** with concise medical reasoning.

This repository accompanies the poster presentation at **:contentReference[oaicite:0]{index=0} 2026**, hosted at **:contentReference[oaicite:1]{index=1}**.

---

## Motivation

- Diabetes-related misinformation spreads rapidly in short Arabic videos  
- Manual verification is slow and inaccessible to most viewers  
- Most automated fact-checking systems focus on **English text**, not **Arabic medical video content**

MythBuster addresses this gap by combining speech-to-text, claim extraction, retrieval, and reasoning into a single automated pipeline.

---

## System Overview

**End-to-end pipeline:**

1. **Video ingestion**  
   User submits a short YouTube video URL (≤ 2 minutes)

2. **Speech-to-text (STT)**  
   Arabic speech is transcribed into text

3. **Claim extraction**  
   Medically relevant diabetes claims are extracted from the transcript

4. **Evidence retrieval**  
   - Trusted medical web sources (domain-filtered search)  
   - Scientific literature via Retrieval-Augmented Generation (RAG)

5. **Verdict generation**  
   Claims are classified and explained with Arabic medical reasoning

---

## Verdict Labels

Each extracted claim receives one of the following verdicts:

- **TRUE**
- **FALSE**
- **PARTIALLY TRUE**
- **INSUFFICIENT INFO**

Each verdict is accompanied by:
- Concise Arabic medical explanation  
- Supporting evidence with source links  

---

## Results & Key Findings

- **Arabic STT quality:** Benchmarking across multiple models showed that **Whisper-Large** consistently achieved the highest transcription quality for Arabic health videos, outperforming **Whisper-Medium**, **GPT-4o**, and **GPT-4o-mini**.

- **Effect of retrieval grounding and system design:** Incorporating **trusted web search and Retrieval-Augmented Generation (RAG)** significantly improved claim verification reliability compared to LLM-only baselines. With evidence grounding enabled, the final pipeline produced **structured, evidence-grounded verdicts with concise Arabic medical reasoning**, achieving **near–expert-level performance** that approached the quality of a **GPT-5–based LLM-as-Judge evaluation**, while robustly handling edge cases such as non-diabetes videos and input constraints.


---

## Key Contributions

- End-to-end Arabic video fact-checking (**URL → verdict**)  
- Hybrid evidence grounding: trusted web search + RAG over scientific literature  
- Structured, explainable outputs with Arabic medical reasoning  
- Robust system design with input validation, caching, and clear error handling  

---

## Tech Stack & Key Components

- **Speech-to-text:** Whisper-Large (Arabic STT)  
- **Claim extraction:** Gemini 1.5 Flash (structured JSON outputs)  
- - **Fact-checking:** Hybrid retrieval-based verification combining domain-filtered web search with RAG over an arXiv-based research corpus (ChromaDB) 
- **Web search:** Serper.dev (trusted, domain-filtered sources)  
- **RAG:** ChromaDB over a curated research corpus  
- **Embeddings:** all-MiniLM-L6-v2 (Sentence Transformers)  
- **Backend:** FastAPI  
- **Frontend:** React  
- **Database:** PostgreSQL (result caching & storage)  
- **Deployment:** Docker (full-stack containerized setup)

---

## Project Status

- **Type:** Research prototype / demo system  
- **Presented at:** MENA ML Winter School 2026 (KAUST)  
- **Focus:** Applied ML + full-stack system design for medical misinformation  

This repository is intended for **demonstration and discussion**, not as a production-ready service.

---

## Contact

**Ahmed Saleh Ahmed Akhtarulzaman**  
📧 asaazamaan@gmail.com  
🔗 GitHub: https://github.com/asaazamaan  

---

## License

This project is licensed under the **MIT License**.
