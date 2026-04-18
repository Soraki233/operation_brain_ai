from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncIterator, Iterable, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI

from core.settings import settings
from db.session import AsyncSession
from db.models import ChatMessage as ChatMessageModel
from db.models import KnowledgeFile as KnowledgeFileModel
from repository.knowledge_repo import KnowledgeRepo
from service.vector_store_service import VectorStoreService


logger = logging.getLogger(__name__)


class AgentService:
    """
    RAG Agent：
    - 基座模型走 DashScope 的 OpenAI 兼容协议（ChatOpenAI）。
    - retrieve 用 PGVector 做向量召回，按 kb_ids 过滤。
    - astream_answer 以 async generator 形式逐 token 产出，供 SSE 使用。
    模型、温度、最大 token、提示词等均由 core.settings 统一管理。
    """

    # assistant context 引用片段最大保留字符数（避免超长上下文）
    _SNIPPET_MAX_CHARS = 600

    def __init__(self) -> None:
        self._llm = ChatOpenAI(
            model=settings.QWEN_CHAT_MODEL,
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
            temperature=settings.AGENT_TEMPERATURE,
            max_tokens=settings.AGENT_MAX_TOKENS,
            streaming=True,
        )
        self._vector_store = VectorStoreService().get_store()

    # ------------------------------- 检索 -------------------------------

    async def retrieve(
        self,
        question: str,
        *,
        kb_ids: Optional[Iterable[str]],
        db: AsyncSession,
    ) -> tuple[list[dict], str]:
        """
        返回 (citations, context_text)。
        - citations：供前端展示的引用来源，也会写入 assistant 消息的 meta_json。
        - context_text：拼接后的知识库上下文，送入 LLM。
        """
        kb_id_list = [kb for kb in (kb_ids or []) if kb]
        top_k = settings.KNOWLEDGE_RETRIEVE_TOP_K
        q_preview = question.replace("\n", " ")[:60]

        # 优先尝试在 pgvector 侧做 kb_id 过滤；若 langchain-postgres 版本不支持 $in，
        # 则退化为不过滤 + Python 端过滤。
        def _search() -> list[tuple]:
            try:
                filter_ = {"kb_id": {"$in": kb_id_list}} if kb_id_list else None
                return self._vector_store.similarity_search_with_score(
                    question, k=top_k, filter=filter_
                )
            except Exception:
                logger.exception(
                    "PGVector filter 失败，退化为无过滤召回后在 Python 端过滤"
                )
                return self._vector_store.similarity_search_with_score(
                    question, k=top_k
                )

        t_vec_start = time.perf_counter()
        raw_hits = await asyncio.to_thread(_search)
        vec_elapsed_ms = (time.perf_counter() - t_vec_start) * 1000
        logger.info(
            "[RAG] 向量检索 | top_k=%d kb=%d 返回=%d 耗时=%.1fms | q=%r",
            top_k,
            len(kb_id_list),
            len(raw_hits),
            vec_elapsed_ms,
            q_preview,
        )

        # 距离阈值过滤 + kb 过滤（兜底）
        kb_id_set = set(kb_id_list)
        hits: list[tuple] = []
        for doc, score in raw_hits:
            if score is not None and score > settings.AGENT_RAG_SCORE_MAX_DISTANCE:
                continue
            if kb_id_set and (doc.metadata or {}).get("kb_id") not in kb_id_set:
                continue
            hits.append((doc, score))

        logger.info(
            "[RAG] 阈值过滤 | 阈值=%.2f 原始=%d 保留=%d",
            settings.AGENT_RAG_SCORE_MAX_DISTANCE,
            len(raw_hits),
            len(hits),
        )

        if not hits:
            return [], ""

        # 批量补齐 file_name
        t_meta_start = time.perf_counter()
        file_id_set = {(doc.metadata or {}).get("file_id") for doc, _ in hits}
        file_id_set.discard(None)
        file_name_map: dict[str, str] = {}
        for fid in file_id_set:
            kf: (
                KnowledgeFileModel | None
            ) = await KnowledgeRepo.get_knowledge_file_by_id(fid, db)
            file_name_map[fid] = kf.file_name if kf else "（已删除）"
        meta_elapsed_ms = (time.perf_counter() - t_meta_start) * 1000
        logger.info(
            "[RAG] 补齐文件名 | 文件数=%d 耗时=%.1fms",
            len(file_id_set),
            meta_elapsed_ms,
        )

        citations: list[dict] = []
        context_lines: list[str] = []
        for idx, (doc, score) in enumerate(hits, start=1):
            meta = doc.metadata or {}
            file_id = meta.get("file_id") or ""
            chunk_index = int(meta.get("chunk_index", 0))
            file_name = file_name_map.get(file_id, "（已删除）")
            content = (doc.page_content or "").strip()
            snippet = content[: self._SNIPPET_MAX_CHARS]
            if len(content) > self._SNIPPET_MAX_CHARS:
                snippet += "…"

            citations.append(
                {
                    "file_id": file_id,
                    "file_name": file_name,
                    "chunk_index": chunk_index,
                    "score": float(score) if score is not None else 0.0,
                    "snippet": snippet,
                }
            )
            context_lines.append(f"[#{idx} {file_name}] {snippet}")

        context_text = "\n\n".join(context_lines)
        return citations, context_text

    # ------------------------------- 生成 -------------------------------

    @staticmethod
    def _history_to_messages(
        history: list[ChatMessageModel],
    ) -> list[BaseMessage]:
        """把 DB 里的历史消息转成 LangChain Message，忽略空内容。"""
        msgs: list[BaseMessage] = []
        for m in history:
            if not m.content:
                continue
            if m.role == "user":
                msgs.append(HumanMessage(content=m.content))
            elif m.role == "assistant":
                msgs.append(AIMessage(content=m.content))
            elif m.role == "system":
                msgs.append(SystemMessage(content=m.content))
        return msgs

    def build_messages(
        self,
        history: list[ChatMessageModel],
        context: str,
        question: str,
    ) -> list[BaseMessage]:
        messages: list[BaseMessage] = [
            SystemMessage(content=settings.AGENT_SYSTEM_PROMPT),
        ]
        messages.extend(self._history_to_messages(history))
        if context:
            messages.append(
                SystemMessage(content=f"以下是从知识库中检索到的相关片段：\n{context}")
            )
        messages.append(HumanMessage(content=question))
        return messages

    async def astream_answer(
        self,
        history: list[ChatMessageModel],
        context: str,
        question: str,
    ) -> AsyncIterator[str]:
        """逐 token 流出回答文本，并在终端打印首 token 耗时（TTFT）+ 总耗时。"""
        messages = self.build_messages(history, context, question)
        # prompt 粗略规模，方便对比耗时
        prompt_chars = sum(
            len(m.content) if isinstance(m.content, str) else 0 for m in messages
        )

        t_start = time.perf_counter()
        first_token_at: float | None = None
        total_chars = 0
        logger.info(
            "[LLM] 开始流式 | 模型=%s 历史=%d 上下文=%dchar prompt≈%dchar",
            settings.QWEN_CHAT_MODEL,
            len(history),
            len(context),
            prompt_chars,
        )

        try:
            async for chunk in self._llm.astream(messages):
                text = getattr(chunk, "content", None)
                if not text:
                    continue
                # ChatOpenAI 流式 chunk.content 偶尔是 list（工具消息等），做下兜底
                if isinstance(text, list):
                    text = "".join(
                        part.get("text", "") if isinstance(part, dict) else str(part)
                        for part in text
                    )
                if first_token_at is None:
                    first_token_at = time.perf_counter()
                    logger.info(
                        "[LLM] 首 token 到达 (TTFT) 耗时=%.1fms",
                        (first_token_at - t_start) * 1000,
                    )
                total_chars += len(text)
                yield text
        finally:
            total_ms = (time.perf_counter() - t_start) * 1000
            ttft_ms = (first_token_at - t_start) * 1000 if first_token_at else -1
            logger.info(
                "[LLM] 流式完成 | TTFT=%.1fms 总耗时=%.1fms 输出=%dchar",
                ttft_ms,
                total_ms,
                total_chars,
            )
