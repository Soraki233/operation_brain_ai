from __future__ import annotations

from pathlib import Path
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
)

from service.vector_store_service import VectorStoreService


class KnowledgeIngestService:
    def __init__(self) -> None:
        self.vector_store = VectorStoreService().get_store()

    def load_file(self, file_path: str) -> List[Document]:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            docs = PyPDFLoader(str(path)).load()
        elif suffix == ".docx":
            docs = Docx2txtLoader(str(path)).load()
        elif suffix in {".xlsx", ".xls"}:
            docs = UnstructuredExcelLoader(str(path), mode="elements").load()
        elif suffix in {".md", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            docs = [Document(page_content=text, metadata={"source": str(path)})]
        else:
            raise ValueError(f"暂不支持的文件类型: {suffix}")

        cleaned_docs: List[Document] = []
        for doc in docs:
            content = (doc.page_content or "").strip()
            if not content:
                continue
            cleaned_docs.append(
                Document(
                    page_content=content,
                    metadata=doc.metadata or {},
                )
            )
        return cleaned_docs

    def split_documents(
        self,
        docs: List[Document],
        *,
        kb_id: str,
        file_id: str,
    ) -> List[Document]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=120,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
        )

        normalized_docs: List[Document] = []
        for doc in docs:
            metadata = dict(doc.metadata or {})
            metadata.update(
                {
                    "kb_id": kb_id,
                    "file_id": file_id,
                }
            )
            normalized_docs.append(
                Document(
                    page_content=doc.page_content,
                    metadata=metadata,
                )
            )

        chunks = splitter.split_documents(normalized_docs)

        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx

        return chunks

    def ingest_file(
        self,
        *,
        kb_id: str,
        file_id: str,
        file_path: str,
    ) -> dict:
        raw_docs = self.load_file(file_path)
        if not raw_docs:
            return {
                "chunk_count": 0,
                "message": "文件没有可入库内容",
            }

        chunks = self.split_documents(
            raw_docs,
            kb_id=kb_id,
            file_id=file_id,
        )

        ids = [f"{file_id}:{i}" for i in range(len(chunks))]
        self.vector_store.add_documents(documents=chunks, ids=ids)

        return {
            "chunk_count": len(chunks),
            "message": "文件入库成功",
        }

    def delete_file_vectors(self, *, file_id: str, chunk_count: int) -> None:
        if chunk_count <= 0:
            return
        ids = [f"{file_id}:{i}" for i in range(chunk_count)]
        self.vector_store.delete(ids=ids)