from langchain_postgres import PGVector
from langchain_community.embeddings import DashScopeEmbeddings

from core.settings import settings

# 获取向量数据库
class VectorStoreService:
    def __init__(self) -> None:
        self.embeddings = DashScopeEmbeddings(
            model=settings.QWEN_EMBEDDING_MODEL,
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
        )

    def get_store(self) -> PGVector:
        return PGVector(
            embeddings=self.embeddings,
            collection_name="knowledge_chunks",
            connection=settings.VECTOR_DATABASE_URL,
            use_jsonb=True,
        )