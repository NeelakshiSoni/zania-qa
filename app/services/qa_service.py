
import asyncio
import hashlib
import json
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from app.services.retriever import retrieve_relevant_chunks
from app.services.database import (
    get_history,
    save_message,
    get_cached_answer,
    cache_answer,
)

import logging

logger = logging.getLogger("zania.qa")
NOT_FOUND = "Not found in the provided document."
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    timeout=30,
    max_retries=1,
)
llm_semaphore = asyncio.Semaphore(5)


async def answer_question(vector_store, document_id, session_id, question):
    history = await get_history(session_id, limit=6)

    cache_material = json.dumps(
        [document_id, question.strip().casefold(), history],
        sort_keys=True,
    )
    cache_key = hashlib.sha256(cache_material.encode()).hexdigest()

    cached = await get_cached_answer(cache_key)
    if cached:
        answer, citations_json = cached
    else:
        chunks = await asyncio.to_thread(
            retrieve_relevant_chunks, vector_store, question
        )
        print("QUESTION:", repr(question))
        print("RETRIEVED CHUNKS:")
        for chunk in chunks:
            print(chunk.metadata)
            print(chunk.page_content)

       

        context = "\n\n".join(
            f"[Source: {d.metadata.get('source', 'document')}, "
            f"Page: {d.metadata.get('page', 'N/A')}]\n{d.page_content}"
            for d in chunks
        )

        messages = [
            (
                "system",
                "Answer using only the document context. Use chat history "
                "to understand follow-up questions, but never treat it as "
                "evidence about the document. If the document does not "
                f"support an answer, respond exactly: {NOT_FOUND} "
                "Do not invent facts. Cite source and page when available."
            )
        ]

        messages.extend((m["role"], m["content"]) for m in history)
        messages.append((
            "human",
            f"Document context:\n{context}\n\nQuestion: {question}",
        ))

        async with llm_semaphore:
            response = await llm.ainvoke(messages)

        usage = response.usage_metadata or {}

        logger.info(
            "llm_usage",
            extra={
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        )

        
        answer = response.content
        seen = set()
        citations = []

        for d in chunks:
            citation = {
                "source": d.metadata.get("source"),
                "page": d.metadata.get("page"),
            }
            key = (citation["source"], citation["page"])

            if key not in seen:
                seen.add(key)
                citations.append(citation)

            citations_json = json.dumps(citations)
                

        await cache_answer(cache_key, answer, citations_json)

    await save_message(session_id, "human", question)
    await save_message(session_id, "assistant", answer)

    return {
        "session_id": session_id,
        "question": question,
        "answer": answer,
        "citations": json.loads(citations_json),
        "cached": bool(cached),
    }
