# Zania Document Q&A

A document question-answering application built with FastAPI, React, LangChain, OpenAI, and Chroma. Upload a PDF or JSON document and ask questions about its contents through a web interface.

## Features

- **Document upload:** Supports PDF and JSON files.
- **Text processing:** Extracts document text and splits it into overlapping chunks.
- **Semantic retrieval:** Uses OpenAI embeddings and Chroma to retrieve relevant document chunks.
- **Question answering:** Uses an OpenAI chat model to answer questions using retrieved document context.
- **Source citations:** Returns source metadata, including filenames and page numbers when available.
- **Conversation history:** Stores chat sessions and messages in SQLite.
- **Answer caching:** Caches answers for one hour to avoid repeated LLM calls for matching requests.
- **Input validation:** Validates chat requests and rejects unsupported file types and oversized uploads.
- **Concurrency control:** Uses asynchronous operations and a semaphore to limit concurrent LLM calls.
- **Observability:** Logs API request latency and LLM token usage in JSON format.
- **Automated tests:** Includes tests for document loading and request schema validation.

## Architecture

```text
React Frontend
      |
      v
FastAPI Backend
      |
      +--> Document Loader
      |       +--> PDF / JSON parsing
      |       +--> Text chunking
      |
      +--> OpenAI Embeddings
      |       |
      |       v
      |     Chroma Vector Store
      |
      +--> Retriever
      |       |
      |       v
      |     OpenAI Chat Model
      |
      +--> SQLite
              +--> Sessions
              +--> Messages
              +--> Answer Cache
```

## Technology Stack

- **Frontend:** React, Vite
- **Backend:** Python, FastAPI, Uvicorn
- **LLM integration:** LangChain and OpenAI
- **Vector database:** Chroma
- **Metadata and conversation storage:** SQLite
- **Document processing:** pypdf and LangChain text splitters
- **Testing:** pytest

## Prerequisites

- Python 3.11
- Node.js and npm
- An OpenAI API key

## Local Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd zania-qa
```

### 2. Configure the backend

Create and activate a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
```

Never commit `.env` or expose your API key.

### 3. Start the backend

```bash
uvicorn app.main:app --reload
```

The backend API runs at `http://127.0.0.1:8000`.

Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 4. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## API Endpoints

### `POST /documents`

Uploads a PDF or JSON file, processes its contents, and indexes the resulting chunks.

Example response:

```json
{
  "document_id": "generated-document-id",
  "filename": "sample.json",
  "chunks_indexed": 1
}
```

### `POST /chat`

Accepts a document ID, a question, and an optional session ID.

Example request:

```json
{
  "document_id": "generated-document-id",
  "question": "Where is the company headquartered?"
}
```

The response includes the session ID, answer, citations, and whether the answer was cached.

### `GET /docs`

Provides interactive Swagger API documentation.

## Testing

Run the document loader tests:

```bash
python -m pytest -q tests/test_document_loader.py
```

Run the request schema tests:

```bash
python -m pytest -q tests/test_schemas.py
```

Run the complete test suite:

```bash
python -m pytest -q
```

## Performance and Observability

- Request middleware records HTTP method, path, status code, and processing duration.
- JSON logs record request completion and LLM token usage when provided by the model response.
- A semaphore limits concurrent LLM calls.
- Answer caching reduces repeated model calls.
- Document chunking and vector similarity search support retrieval over larger documents.

## Data and Configuration

- `chroma_db/`: Persistent vector-store data.
- `data/`: SQLite database and related application data.
- `.env`: Local secrets and configuration; should not be committed.
- `.env.example`: Example configuration using placeholder values.

Back up persistent data directories if you need to retain indexed documents or chat history.

## Limitations and Future Improvements

- Improve retrieval relevance and citation accuracy through evaluation and tuning.
- Add automated API integration tests and concurrency tests.
- Add Docker and Docker Compose for reproducible deployment.
- Expand observability with latency distributions and cost monitoring.
- Evaluate support for multiple questions in a single request if required by the project specification.

## License

Add the applicable license before distributing this project.
