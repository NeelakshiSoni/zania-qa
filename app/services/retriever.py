
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

PERSIST_DIRECTORY = "./chroma_db"


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model="text-embedding-3-small")


def create_vector_store(
    chunks: list[Document],
    document_id: str,
) -> Chroma:
    return Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=f"doc_{document_id.replace('-', '')}",
        persist_directory=PERSIST_DIRECTORY,
    )


def get_vector_store(document_id: str) -> Chroma:
    store = Chroma(
        collection_name=f"doc_{document_id.replace('-', '')}",
        embedding_function=get_embeddings(),
        persist_directory=PERSIST_DIRECTORY,
    )

    if not store.get(limit=1).get("ids"):
        raise ValueError("Document not found.")

    return store


def retrieve_relevant_chunks(
    vector_store: Chroma,
    question: str,
    k: int = 10,
) -> list[Document]:
    return vector_store.similarity_search(question, k=10)