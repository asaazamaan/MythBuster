# Project Fact_Checker
Fact_Checker is an innovative platform for.......

 #### project structure

- React frontend
- Python backend API server
- PostgreSQL database
- pgAdmin for database management
- Database initialization scripts
- Docker Compose
- RAG (Retrieval Augmented Generation) system with ChromaDB for fact-checking

## Services

| Service              | URL                                 | Description                           |
|----------------------|-------------------------------------|---------------------------------------|
| PostgreSQL           | `postgres://localhost:5432`         | Main application database             |
| pgAdmin              | `http://localhost:5050`             | Database management interface         |
| React App            | `http://localhost:3000`             | Frontend web application              |
| FastAPI API Server   | `http://localhost:4000`             | Backend API with RAG integration     |
| ChromaDB             | Local file storage in `.chromadb/`  | Vector database for medical knowledge |

## Usage

- Copy the example environment file to create your .env file:

```shell
cp example.env .env
```

- Start the containers:

```shell
docker compose up
```

## Database Initialization

To create and populate database tables:
1. Edit the SQL scripts in the db-init-scripts/ directory:
  - `01_init_db.sql`: Create tables
  - `02_insert_db.sql`: Insert initial data

2. Rebuild the containers with the new scripts:

> **Caution:** This will stop all running containers, and remove all named volumes declared in the "volumes" section as well as all anonymous volumes attached to containers.

```shell
docker compose down -v
docker compose up --build db
```

3. Verify that all four containers are running:
```shell
docker ps
```
If any container is not running, check the logs:
```shell
docker ps -a
docker logs <id_of_the_stopped_container>
```

## Developing the API locally

You should use an en
### Adding dependencies to the API service

If you `pip install` a package in the API service, you need to update the `requirements.txt`:

```shell
pip freeze > requirements.txt
```

and then restart the api container:

```shell
docker compose down
docker compose up --build api
```

## RAG System Setup (ChromaDB & Medical Knowledge Base)

The project includes a RAG (Retrieval Augmented Generation) system that uses ChromaDB to store and query medical information for fact-checking claims about health topics.

### Setting up the RAG Virtual Environment

1. Navigate to the RAG directory:
```shell
cd rag/
```

2. Create and activate a Python virtual environment:
```shell
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```shell
pip install -r requirements.txt
```

> **Note:** The RAG system uses ChromaDB v0.4.22 and NumPy v1.24.3 for compatibility. These specific versions are required for proper functioning.

### ChromaDB Knowledge Base Setup

1. **Index Medical Sources (trusted sites)**:
```shell
cd rag/
source venv/bin/activate
python index_from_url.py
```

1b. **Optional: Index arXiv papers (same collection, equal weight)**:
```shell
cd rag/
source venv/bin/activate
python index_from_arxiv.py
```
- This will fetch up to 150 arXiv papers for “diabetes” and index full PDF text when available (fallback to abstracts). Data is stored in the same ChromaDB collection with metadata, no special weighting.

2. **Test ChromaDB Setup**: Verify that the knowledge base is properly indexed:
```shell
python test_chromadb.py
```

3. **ChromaDB Data Persistence**: The ChromaDB database is stored in `.chromadb/` directory at the project root. This ensures data persistence across container restarts.

### RAG System Components

- **`utils.py`**: Core utilities for web scraping, text chunking, embeddings, and ChromaDB operations
- **`index_from_url.py`**: Script to index medical content from URLs listed in `diabet_urls.txt`
- **`index_from_arxiv.py`**: Script to index arXiv titles/abstracts or full PDFs into the same collection
- **`test_chromadb.py`**: Test script to verify ChromaDB functionality and search capabilities
- **`diabet_urls.txt`**: List of trusted medical sources for diabetes-related information
- **`requirements.txt`**: All Python dependencies with exact versions for the RAG environment

### RAG Integration with API

The RAG system is integrated into the main API through:
- Medical claim fact-checking with source citations
- Similarity search using sentence transformers
- Multi-language support (Arabic to English translation)
- Source relevance scoring and user-friendly displays

### Troubleshooting RAG Setup

If you encounter issues:

1. **ChromaDB Version Error**: Ensure you're using ChromaDB 0.4.22, not newer versions
2. **NumPy Compatibility**: Use NumPy 1.24.3 for compatibility with ChromaDB 0.4.22
3. **Empty Database**: Run `index_from_url.py` to populate the knowledge base
4. **Permission Issues**: Ensure `.chromadb/` directory has proper write permissions

## Managing Secrets and Environment Variables

- For production environments, use Docker secrets:
  - Edit the `docker-compose.yml` file
  - Add a secrets attribute under each service that requires secure data.
  ```yaml
  version: '3.7'
  services:
    react_app:
      secrets:
        - app_secret

  secrets:
    app_secret:
      file: ./app_secret.txt
  ```

- For development environments, use environment variables:
  - Add variables to the .env file, e.g.:
  ```shell
  API_SERVER_KEY=0123456789abcdefghijklmnopqrstuvwxyz
  ```
  -  Update the docker-compose.yml file to use the environment variables:
  ```yaml
  api:
    environment:
      - API_SERVER_PORT=${API_SERVER_PORT}
      - POSTGRES_HOST=postgres16
      - API_SERVER_KEY=${API_SERVER_KEY}
  ```

## Contribution

- Create a new branch for the feature

```
git branch -b new-feature-name
```
- Push your changes to a remote branch

```
git push origin new-feature-name
```

- Create a PR (Pull Request)
  - Go to Github.com and select the branch you just push
  - Click on *Contribute*, then click *Open Pull Request*

## License
This project is licensed under the MIT License.