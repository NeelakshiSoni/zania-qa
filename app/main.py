import logging
import time
import json


from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.schemas import ChatRequest, ChatResponse
from app.services.database import init_db, create_session
from app.services.retriever import get_vector_store
from app.services.qa_service import answer_question
from uuid import uuid4
from fastapi import UploadFile, File, HTTPException
from app.services.document_loader import load_document
from app.services.retriever import create_vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Zania Document Q&A API", lifespan=lifespan)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key in (
            "method",
            "path",
            "status_code",
            "duration_ms",
            "input_tokens",
            "output_tokens",
            "total_tokens",
        ):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()
root_logger.addHandler(handler)
logger = logging.getLogger("zania.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "request_completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid4())

    try:
        store = get_vector_store(request.document_id)

        if request.session_id:
            # Verify that the session belongs to this document.
            from app.services.database import DB_PATH
            import aiosqlite

            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute(
                    "SELECT document_id FROM sessions WHERE session_id = ?",
                    (session_id,),
                )
                row = await cursor.fetchone()

            if not row or row[0] != request.document_id:
                raise HTTPException(404, "Chat session not found.")

        else:
            await create_session(session_id, request.document_id)

        return await answer_question(
            store,
            request.document_id,
            session_id,
            request.question,
        )

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(404, "Document not found.") from exc
    except Exception as exc:
        import logging
        logging.exception("Question answering failed")
        raise HTTPException(
            status_code=500,
            detail=f"Question answering failed: {type(exc).__name__}: {exc}",
        ) from exc


@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename or ""

    if not filename.lower().endswith((".pdf", ".json")):
        raise HTTPException(400, "Only PDF and JSON files are supported.")

    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "File exceeds the 10 MB limit.")

    try:
        chunks = load_document(content, filename)
        document_id = str(uuid4())
        create_vector_store(chunks, document_id)
        return {
            "document_id": document_id,
            "filename": filename,
            "chunks_indexed": len(chunks),
        }
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
