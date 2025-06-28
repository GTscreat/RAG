1.

python -m venv venv
.\venv\Scripts\Activate.ps1
Եթե չի ստացվում - Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
pip install -r requirements.txt

.\venv\Scripts\python.exe -m pip install ......

2. 
python -m venv .venv
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe -m pip install ......
pip install -r requirements.txt


git status
git add .
git commit -m "update 1"
git push origin master
git status

git pull


# 🇦🇲 Armenian News RAG API

## System Architecture

```
[News API Scraper] 
      │
      ▼
[data_ingestion.py]     # Periodic fetch & save
      │
      ▼
[chunker.py]            # Clean, split, and chunk text
      │
      ▼
[embedding.py]          # Generate dense embeddings
      │
      ▼
[vector_store.py]       # Qdrant: upsert chunks + metadata
      │
      ▼
[retriever.py]          # Hybrid retrieval (dense + BM25 + time)
      │
      ▼
[prompt_templates.py]   # Compose prompt context
      │
      ▼
[llm_client.py]         # LLM (GPT-4, Claude) answer
      │
      ▼
[main.py / api.py]      # FastAPI HTTP API
```

## Pipeline Components

- **Data ingestion (`data_ingestion.py`)**  
  Periodically fetches news data from remote APIs, handles rate limits, saves raw batches.

- **Chunking & Cleaning (`chunker.py`)**  
  Removes HTML/noise, normalizes Armenian text, splits into semantic chunks with metadata.

- **Embedding (`embedding.py`)**  
  Loads Armenian text embedding model (metric-ai/armenian-text-embeddings-1), encodes chunks.

- **Vector DB Storage (`vector_store.py`)**  
  Stores embeddings and metadata in Qdrant; enables fast dense & hybrid search.

- **Retrieval & Ranking (`retriever.py`)**  
  Hybrid retrieval (semantic + keyword + time-decay), applies metadata filters, returns top-K.

- **Prompting (`prompt_templates.py`)**  
  Formats context window for LLM answer, with citation and direct quote instructions.

- **LLM Response (`llm_client.py`)**  
  Calls GPT-4 / Claude / Mistral via API, ensures answers use only retrieved context.

- **FastAPI Server (`main.py`, `api.py`)**  
  Exposes `/query` endpoint for QA over Armenian news.

## Running Locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

- Visit API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Example Query

```bash
curl -X POST "http://127.0.0.1:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Որն է Հայաստանի կառավարության վերջին որոշումը?", "filters": {}}'
```

## Evaluation

Run RAG pipeline evaluation with:

```bash
python evaluate.py
```

## Monitoring (Optional, Demo)

```bash
python monitor.py
```

---

**.env** file (example):

```ini
OPENAI_API_KEY=your-openai-key-here
QDRANT_URL=https://your-qdrant-instance
QDRANT_API_KEY=your-qdrant-api-key-here
```
