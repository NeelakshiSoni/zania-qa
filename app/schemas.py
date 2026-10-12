from pydantic import BaseModel, Field



class ChatRequest(BaseModel):
    document_id: str = Field(min_length=1, max_length=64)
    session_id: str | None = None
    question: str = Field(min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    citations: list[dict]
    cached: bool