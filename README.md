MythBuster: Automated Fact-Checking for Arabic Videos About Diabetes

🔗 Live demo: https://asaazamaan.github.io/mythbuster-demo/

🎥 Demo video: https://www.youtube.com/watch?v=p8ZqCEGbmfs

MythBuster is an end-to-end system that automatically fact-checks diabetes-related medical claims in short Arabic videos.
Given a video URL, the system transcribes spoken Arabic, extracts check-worthy medical claims, retrieves supporting evidence, and produces evidence-grounded Arabic verdicts.

This repository accompanies the poster presentation at MENA ML Winter School 2026 (KAUST).

Motivation

Diabetes-related misinformation spreads rapidly in short Arabic videos.

Manual verification is slow and inaccessible to most viewers.

Most existing automated fact-checking systems focus on English text, not Arabic medical video content.

MythBuster addresses this gap by combining speech-to-text, claim extraction, retrieval, and reasoning into a single automated pipeline.

System Overview

End-to-end pipeline:

Video ingestion
User submits a short YouTube video URL (≤ 2 minutes)

Speech-to-text (STT)
Arabic speech is transcribed into text

Claim extraction
Medically relevant diabetes claims are extracted from the transcript

Evidence retrieval

Trusted medical web sources (domain-filtered search)

Scientific literature via Retrieval-Augmented Generation (RAG)

Verdict generation
Claims are classified and explained with Arabic medical reasoning

Verdict Labels

Each extracted claim receives one of the following verdicts:

TRUE

FALSE

PARTIALLY TRUE

INSUFFICIENT INFO

Each verdict is accompanied by:

Concise Arabic medical explanation

Supporting evidence with source links

Key Contributions

End-to-end Arabic video fact-checking (URL → verdict)

Hybrid evidence grounding: trusted web search + RAG over scientific literature

Structured, explainable outputs with Arabic medical reasoning

Robust system design with input validation, caching, and clear error handling

Tech Stack

Backend: FastAPI

Frontend: React

Database: PostgreSQL (result caching & storage)

Retrieval:

Trusted web search

RAG using ChromaDB over medical literature

Deployment: Docker (full-stack containerized setup)

Demo

A recorded walkthrough demonstrates:

Full end-to-end execution (no mock data)

Multiple verdict types (TRUE, FALSE, PARTIALLY TRUE, INSUFFICIENT INFO)

Domain filtering and input constraint handling

👉 See the demo page:
https://asaazamaan.github.io/mythbuster-demo/

Project Status

Type: Research prototype / demo system

Presented at: MENA ML Winter School 2026 (KAUST)

Focus: Applied ML + full-stack system design for medical misinformation

This repository is intended for demonstration and discussion, not as a production-ready service.

Contact

Ahmed Saleh Ahmed Akhtarulzaman
📧 asaazamaan@gmail.com

🔗 GitHub: https://github.com/asaazamaan

License

This project is licensed under the MIT License.