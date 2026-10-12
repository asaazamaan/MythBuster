# MythBuster: Automated Fact-Checking for Arabic Videos About Diabetes

🔗 **Demo page:** https://asaazamaan.github.io/mythbuster-demo/  
🎥 **Demo video:** https://www.youtube.com/watch?v=p8ZqCEGbmfs  

**MythBuster** is an end-to-end system that automatically fact-checks diabetes-related medical claims in short Arabic videos.

Given a video URL, the system transcribes spoken Arabic, extracts check-worthy medical claims, retrieves supporting evidence, and produces **evidence-grounded Arabic verdicts** with concise medical reasoning.

MythBuster was developed as part of the **KAUST Academy Artificial Intelligence Specialization Graduation Project** and was subsequently presented at **MENA ML Winter School 2026**, hosted at **King Abdullah University of Science and Technology (KAUST), Saudi Arabia**.
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

### Arabic Speech Recognition

Among the evaluated models, **Whisper-Large** achieved the strongest reported Arabic transcription performance, outperforming Whisper-Medium, GPT-4o, and GPT-4o-mini.

### Fact-Checking Evaluation

We compared a baseline configuration against the final evidence-grounded pipeline using a **GPT-5-based LLM-as-a-Judge evaluation protocol**.

The MENA ML 2026 poster reports the following results for matched claims:

| Metric | Baseline | Final Pipeline |
|---|---:|---:|
| Weighted Accuracy | 0.70 | 0.97 |
| Hard Accuracy | 0.55 | 0.94 |
| Macro F1 (weighted) | 0.60 | 0.95 |

The results indicate that integrating trusted web search and Retrieval-Augmented Generation (RAG) improved verdict quality under the reported evaluation protocol compared with the baseline.

**Evaluation limitation:** These results were obtained using an LLM-based evaluation protocol and should not be interpreted as independently validated clinical accuracy.


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
- **Fact-checking:** Hybrid retrieval-based verification with evidence grounding  
- **Retrieval sources:**  
  - Trusted, domain-filtered medical web search (Serper.dev)  
  - RAG over an arXiv-based research corpus (ChromaDB)  
- **Embeddings:** all-MiniLM-L6-v2 (Sentence Transformers)  
- **Backend:** FastAPI  
- **Frontend:** React  
- **Database:** PostgreSQL (result caching & storage)  
- **Deployment:** Docker (full-stack containerized setup)

---

## Project Status

- **Type:** End-to-End AI-Powered Application
- **Developed as:** KAUST Academy Artificial Intelligence Specialization Graduation Project
- **Presented at:**
  - KAUST Academy AI Specialization Graduation Project Presentation
  - MENA ML Winter School 2026 — KAUST, Saudi Arabia
- **Focus:** Full-stack development, LLM integration, Retrieval-Augmented Generation (RAG), and automated Arabic medical fact-checking
  
**Status:** Functional prototype developed and evaluated as an academic project.

---
## Academic Presentations

MythBuster was presented at:

- **KAUST Academy Artificial Intelligence Specialization Graduation Project** — [View Poster](docs/posters/MythBuster_KAUST_Poster.pdf)
- **MENA ML Winter School 2026 (KAUST)** — [View Poster](docs/posters/MythBuster_MenaML_Poster.pdf)
---

## Contact

**Ahmed Saleh Ahmed Akhtarulzaman**  
📧 asaazamaan@gmail.com  
🔗 GitHub: https://github.com/asaazamaan  

---
