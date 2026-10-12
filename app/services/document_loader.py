
import json
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


MAX_CHARS = 2_000_000
MAX_PDF_PAGES = 500


def load_document(content: bytes, filename: str) -> list[Document]:
    if filename.lower().endswith(".pdf"):
        try:
            reader = PdfReader(BytesIO(content), strict=False)

            if reader.is_encrypted:
                raise ValueError(
                    "Password-protected PDFs are not supported."
                )

            if len(reader.pages) > MAX_PDF_PAGES:
                raise ValueError(
                    f"PDF exceeds the {MAX_PDF_PAGES}-page limit."
                )

            documents = []

            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""

                if text.strip():
                    documents.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": filename,
                                "page": i + 1,
                            },
                        )
                    )

        except ValueError:
            raise
        except (PdfReadError, OSError, KeyError) as exc:
            raise ValueError(
                "Could not read this PDF. It may be corrupted or invalid."
            ) from exc

    elif filename.lower().endswith(".json"):
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(
                "Invalid JSON file. Please upload a valid JSON document."
            ) from exc

        text = json.dumps(data, ensure_ascii=False, indent=2)
        documents = [
            Document(
                page_content=text,
                metadata={"source": filename},
            )
        ]

    else:
        raise ValueError("Only PDF and JSON documents are supported.")

    if not documents:
        raise ValueError(
            "The document contains no extractable text."
        )

    total_chars = sum(len(doc.page_content) for doc in documents)

    if total_chars > MAX_CHARS:
        raise ValueError(
            "Document exceeds the 2-million-character limit."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )

    return splitter.split_documents(documents)
