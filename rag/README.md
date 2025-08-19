# RAG System - Medical Fact-Checking Knowledge Base

This directory contains the Retrieval Augmented Generation (RAG) system for medical fact-checking using ChromaDB and sentence transformers.

## Overview

The RAG system provides:
- **Medical Knowledge Base**: Indexed content from trusted medical sources (WHO, CDC, Mayo Clinic)
- **Semantic Search**: Vector similarity search using sentence transformers
- **Fact-Checking Support**: Evidence retrieval for claim verification
- **Multi-language Support**: Arabic-to-English translation pipeline integration

## Quick Start

### 1. Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Index Medical Knowledge Base
```bash
# Populate ChromaDB with medical content
python index_from_url.py
```

### 3. Test Setup
```bash
# Verify ChromaDB functionality
python test_chromadb.py
```
##################Ahmed
cd rag
source ../venv/Scripts/activate   # (Windows: ..\venv\Scripts\activate)
python index_from_url.py
python index_from_arxiv.py
python test_chromadb.py
################################
## File Structure

```
rag/
├── venv/                    # Virtual environment
├── requirements.txt         # Python dependencies
├── utils.py                # Core RAG utilities
├── index_from_url.py       # Knowledge base indexing
├── test_chromadb.py        # Testing and verification
├── diabet_urls.txt         # Medical source URLs
└── README.md               # This file
```

## Core Components

### `utils.py`
Core utilities for RAG operations:
- `fetch_and_chunk()`: Web scraping and text chunking
- `get_embedder()`: Sentence transformer model loading
- `get_chroma_collection()`: ChromaDB client and collection management
- `load_urls_from_file()`: URL list processing

### `index_from_url.py`
Indexes medical content into ChromaDB:
- Fetches content from URLs in `diabet_urls.txt`
- Chunks text into manageable segments
- Generates embeddings using sentence transformers
- Stores in ChromaDB with metadata

### `test_chromadb.py`
Comprehensive testing suite:
- Database connectivity verification
- Document count and retrieval tests
- Semantic search functionality
- Diabetes-specific query testing

### `diabet_urls.txt`
Curated list of medical sources:
- WHO (World Health Organization)
- CDC (Centers for Disease Control)
- Mayo Clinic
- Medical journals and trusted health sites

## Technical Details

### Dependencies
- **ChromaDB 0.4.22**: Vector database (specific version for compatibility)
- **NumPy 1.24.3**: Numerical computing (compatible with ChromaDB 0.4.22)
- **sentence-transformers**: Text embedding generation
- **beautifulsoup4**: Web scraping
- **requests**: HTTP client for fetching web content

### Embedding Model
- **Model**: `all-MiniLM-L6-v2`
- **Dimensions**: 384
- **Language**: Multi-language support
- **Performance**: Optimized for semantic similarity

### ChromaDB Configuration
- **Storage**: Persistent local storage in `.chromadb/` directory
- **Collection**: `medical_facts`
- **Chunk Size**: 300 words per document segment
- **Distance Metric**: Cosine similarity

## Usage Examples

### Indexing New Sources
```python
from utils import fetch_and_chunk, get_embedder, get_chroma_collection
from uuid import uuid4

# Add new medical source
url = "https://example-medical-site.com/diabetes-info"
chunks = fetch_and_chunk(url)
embedder = get_embedder()
collection = get_chroma_collection()

embeddings = embedder.encode(chunks).tolist()
ids = [str(uuid4()) for _ in chunks]
collection.add(documents=chunks, embeddings=embeddings, ids=ids)
```

### Searching Medical Information
```python
from utils import get_embedder, get_chroma_collection

# Search for diabetes information
query = "What are the symptoms of type 2 diabetes?"
embedder = get_embedder()
collection = get_chroma_collection()

query_embedding = embedder.encode([query]).tolist()
results = collection.query(
    query_embeddings=query_embedding,
    n_results=5
)

for doc, distance in zip(results['documents'][0], results['distances'][0]):
    print(f"Distance: {distance:.3f}")
    print(f"Content: {doc[:200]}...")
    print("---")
```

## Integration with Main API

The RAG system integrates with the main FastAPI application through:

1. **Fact-Checking Endpoint**: `/api/fact-check` uses RAG for evidence retrieval
2. **Source Citations**: Returns medical sources with relevance scores
3. **Translation Pipeline**: Supports Arabic-to-English claim processing
4. **Error Handling**: Graceful fallbacks when RAG system is unavailable

## Troubleshooting

### Common Issues

1. **ChromaDB Version Conflicts**
   ```bash
   pip install chromadb==0.4.22 numpy==1.24.3
   ```

2. **Empty Knowledge Base**
   ```bash
   python index_from_url.py
   python test_chromadb.py  # Verify indexing
   ```

3. **Permission Errors**
   ```bash
   chmod -R 755 .chromadb/
   ```

4. **Memory Issues with Large Models**
   - Use smaller chunk sizes in `fetch_and_chunk()`
   - Consider switching to lighter embedding models

### Performance Optimization

- **Batch Processing**: Index multiple URLs in batches
- **Chunking Strategy**: Optimize chunk size for your use case
- **Embedding Caching**: Cache embeddings for frequently queried content
- **Database Maintenance**: Regularly clean up duplicate or outdated content

## Development Workflow

1. **Add New Sources**: Update `diabet_urls.txt` with new medical URLs
2. **Re-index**: Run `python index_from_url.py` to update knowledge base
3. **Test Changes**: Use `python test_chromadb.py` to verify functionality
4. **Integration Testing**: Test with main API endpoints

## Production Considerations

- **Data Backup**: Regularly backup `.chromadb/` directory
- **Monitoring**: Track query performance and accuracy
- **Content Updates**: Schedule regular re-indexing of medical sources
- **Security**: Ensure secure access to medical information
- **Compliance**: Follow medical data handling regulations

## Contributing

When contributing to the RAG system:

1. Follow existing code structure and naming conventions
2. Add comprehensive tests for new functionality
3. Update documentation for new features
4. Ensure compatibility with ChromaDB 0.4.22
5. Test integration with the main API

## License

This RAG system is part of the Fact_Checker project and follows the same MIT License.
