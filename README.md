# GitExplore
An intelligent GitHub RAG system that lets you query any codebase in natural language. Combines structure-aware chunking, hybrid retrieval, and LLM-powered reasoning to return accurate, explainable answers with exact source references.

## Running the API + Frontend

1. Start Qdrant:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

2. Start Ollama with the embedding model:
```bash
ollama serve
ollama pull nomic-embed-text
```

3. Set environment variables:
```bash
export GROQ_API_KEY=...
export COHERE_API_KEY=...
```

4. Start FastAPI:
```bash
uvicorn backend.api.main:app --reload --port 8000
```

5. Start Streamlit:
```bash
cd frontend
streamlit run app.py
```

## Frontend

Run the Streamlit frontend:

```bash
streamlit run frontend/app.py
```

Configure the backend URL with:

```bash
GITEXPLORE_API_BASE_URL=http://localhost:8000
```
