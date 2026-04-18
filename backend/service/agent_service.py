from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from typing import AsyncIterator, Iterable, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI
from sqlalchemy import text

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

    # 前端展示（气泡里的引用卡片）的片段最大字符数，避免 UI 拥挤
    _SNIPPET_MAX_CHARS = 600
    # 送入 LLM 的全部知识库上下文的总长上限；单个 chunk 不再截断，
    # 避免模型读到 "……" 省略号直接回一句 "片段在此处截断"。
    # 累加超过此阈值时，仅丢弃后续（相关性更低的）chunk。
    _CONTEXT_TOTAL_MAX_CHARS = 16000

    def __init__(self) -> None:
        self._llm = ChatOpenAI(
            model=settings.QWEN_CHAT_MODEL,
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
            temperature=settings.AGENT_TEMPERATURE,
            max_tokens=settings.AGENT_MAX_TOKENS,
            streaming=True,
        )
        # 证据阅读专用 LLM：temperature=0 保证分析稳定，streaming=True 供前端"思考"展示
        self._evidence_llm = ChatOpenAI(
            model=settings.QWEN_CHAT_MODEL,
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
            temperature=0,
            max_tokens=settings.AGENT_EVIDENCE_MAX_TOKENS,
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
        - citations：供前端展示的引用来源（仅向量命中的 chunk）。
        - context_text：向量命中 chunk + 前后扩读的邻近 chunk 拼成的上下文，送入 LLM。
        """
        kb_id_list = [kb for kb in (kb_ids or []) if kb]
        top_k = settings.KNOWLEDGE_RETRIEVE_TOP_K
        q_preview = question.replace("\n", " ")[:60]

        # 向量搜索（优先带 kb_id 过滤，不支持时退化为 Python 端过滤）
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

        # 补齐 file_name（只查命中的文件）
        t_meta_start = time.perf_counter()
        file_id_set = {(doc.metadata or {}).get("file_id") for doc, _ in hits}
        file_id_set.discard(None)
        file_name_map: dict[str, str] = {}
        for fid in file_id_set:
            kf: KnowledgeFileModel | None = await KnowledgeRepo.get_knowledge_file_by_id(
                fid, db
            )
            file_name_map[fid] = kf.file_name if kf else "（已删除）"
        meta_elapsed_ms = (time.perf_counter() - t_meta_start) * 1000
        logger.info(
            "[RAG] 补齐文件名 | 文件数=%d 耗时=%.1fms",
            len(file_id_set),
            meta_elapsed_ms,
        )

        # ── Citations（仅向量命中）──────────────────────────────────────────
        # 同时记录命中的 (file_id, chunk_index) 用于后续去重标记
        citations: list[dict] = []
        hit_keys: set[tuple[str, int]] = set()
        # 记录 (file_id, chunk_index) → structure_title，后续扩读上下文时复用
        structure_title_map: dict[tuple[str, int], str] = {}
        for doc, score in hits:
            meta = doc.metadata or {}
            file_id = meta.get("file_id") or ""
            chunk_index = int(meta.get("chunk_index", 0))
            file_name = file_name_map.get(file_id, "（已删除）")
            structure_title = str(meta.get("structure_title") or "").strip()
            content = (doc.page_content or "").strip()
            snippet = content[: self._SNIPPET_MAX_CHARS]
            if len(content) > self._SNIPPET_MAX_CHARS:
                snippet += "…"
            citation: dict = {
                "file_id": file_id,
                "file_name": file_name,
                "chunk_index": chunk_index,
                "score": float(score) if score is not None else 0.0,
                "snippet": snippet,
            }
            if structure_title:
                citation["structure_title"] = structure_title
                structure_title_map[(file_id, chunk_index)] = structure_title
            citations.append(citation)
            hit_keys.add((file_id, chunk_index))

        # ── 上下文扩读：取命中 chunk 的前后邻近 chunk ──────────────────────
        window = settings.AGENT_RAG_CONTEXT_WINDOW
        t_expand_start = time.perf_counter()
        expanded_chunks = await self._fetch_context_chunks(hits, window=window, db=db)
        expand_elapsed_ms = (time.perf_counter() - t_expand_start) * 1000
        logger.info(
            "[RAG] 上下文扩读 | window=±%d 命中=%d 扩后=%d 耗时=%.1fms",
            window,
            len(hits),
            len(expanded_chunks),
            expand_elapsed_ms,
        )

        # ── 拼接送 LLM 的上下文（按文件分组 + chunk_index 排序）──────────
        # 格式：每个文件一个连续段落，命中 chunk 加 ★ 标记帮助模型定位
        context_used_chars = 0
        context_skipped = 0

        # 按 file_id 分组
        # chunk 元组：(chunk_index, content, is_hit, structure_title)
        file_chunks: dict[str, list[tuple[int, str, bool, str]]] = defaultdict(list)
        for file_id, chunk_index, content, structure_title in expanded_chunks:
            is_hit = (file_id, chunk_index) in hit_keys
            # 优先使用扩读时从 DB 读到的 structure_title；没有则退回命中 chunk 的标题
            title = structure_title or structure_title_map.get(
                (file_id, chunk_index), ""
            )
            file_chunks[file_id].append((chunk_index, content, is_hit, title))

        context_blocks: list[str] = []
        for file_id, chunk_list in file_chunks.items():
            file_name = file_name_map.get(file_id, "（已删除）")
            # 已经由 _fetch_context_chunks 按 chunk_index 排好序
            lines: list[str] = [f"【文件：{file_name}】"]
            for _, content, is_hit, title in chunk_list:
                marker = "★ " if is_hit else ""
                title_prefix = f"[章节：{title}] " if title else ""
                block = f"{marker}{title_prefix}{content}"
                if context_used_chars + len(block) + len(file_name) + 10 <= self._CONTEXT_TOTAL_MAX_CHARS:
                    lines.append(block)
                    context_used_chars += len(block)
                else:
                    context_skipped += 1
            if len(lines) > 1:
                context_blocks.append("\n".join(lines))

        logger.info(
            "[RAG] 拼接上下文 | 引用=%d 送LLM块=%d 丢弃=%d 总长=%dchar (上限=%d)",
            len(citations),
            sum(len(b.split("\n")) - 1 for b in context_blocks),
            context_skipped,
            context_used_chars,
            self._CONTEXT_TOTAL_MAX_CHARS,
        )

        context_text = "\n\n".join(context_blocks)
        return citations, context_text

    @staticmethod
    async def _fetch_context_chunks(
        hits: list[tuple],
        *,
        window: int,
        db: AsyncSession,
    ) -> list[tuple[str, int, str, str]]:
        """根据命中 chunk 向前/后各扩 window 个相邻 chunk，从 DB 批量查询。

        返回按 (file_id, chunk_index) 排序的列表：
            [(file_id, chunk_index, content, structure_title), ...]
        已自动合并同一文件内重叠的窗口区间，结果去重。
        """
        if window <= 0:
            # 不扩展，直接返回命中 chunk 本身
            result: list[tuple[str, int, str, str]] = []
            for doc, _ in hits:
                meta = doc.metadata or {}
                fid = meta.get("file_id") or ""
                cidx = int(meta.get("chunk_index", 0))
                content = (doc.page_content or "").strip()
                title = str(meta.get("structure_title") or "").strip()
                result.append((fid, cidx, content, title))
            return sorted(result, key=lambda x: (x[0], x[1]))

        # 按 file_id 分组，合并重叠区间
        file_ranges: dict[str, tuple[int, int]] = {}
        for doc, _ in hits:
            meta = doc.metadata or {}
            fid = meta.get("file_id") or ""
            if not fid:
                continue
            cidx = int(meta.get("chunk_index", 0))
            lo, hi = cidx - window, cidx + window
            if fid in file_ranges:
                prev_lo, prev_hi = file_ranges[fid]
                file_ranges[fid] = (min(prev_lo, lo), max(prev_hi, hi))
            else:
                file_ranges[fid] = (lo, hi)

        if not file_ranges:
            return []

        # 构建批量 SQL：每个文件一段 OR 条件
        conditions: list[str] = []
        params: dict = {}
        for i, (fid, (lo, hi)) in enumerate(file_ranges.items()):
            conditions.append(
                f"(lpe.cmetadata->>'file_id' = :fid{i} "
                f"AND (lpe.cmetadata->>'chunk_index')::int BETWEEN :lo{i} AND :hi{i})"
            )
            params[f"fid{i}"] = fid
            params[f"lo{i}"] = max(lo, 0)  # chunk_index 不能为负
            params[f"hi{i}"] = hi

        sql = text(
            f"""
            SELECT lpe.document, lpe.cmetadata
            FROM langchain_pg_embedding lpe
            WHERE lpe.collection_id = (
                SELECT uuid FROM langchain_pg_collection
                WHERE name = 'knowledge_chunks'
            )
            AND ({' OR '.join(conditions)})
            ORDER BY
                lpe.cmetadata->>'file_id',
                (lpe.cmetadata->>'chunk_index')::int
            """
        ).bindparams(**params)

        rows = (await db.execute(sql)).fetchall()

        seen: set[tuple[str, int]] = set()
        result: list[tuple[str, int, str, str]] = []
        for document, cmetadata in rows:
            meta = cmetadata or {}
            fid = meta.get("file_id") or ""
            cidx = int(meta.get("chunk_index", 0))
            key = (fid, cidx)
            if key in seen:
                continue
            seen.add(key)
            title = str(meta.get("structure_title") or "").strip()
            result.append((fid, cidx, (document or "").strip(), title))

        return result

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

    # ------------------------------- 证据阅读 -------------------------------

    async def astream_evidence(
        self,
        question: str,
        context_text: str,
    ) -> AsyncIterator[str]:
        """第三步：流式阅读证据。

        对扩展后的上下文片段逐一分析相关性并提炼关键事实，
        以 async generator 形式逐 token 产出（供前端"思考气泡"实时展示）。
        完整文本由调用方 buffer 收集后用于最终 prompt。
        """
        evidence_prompt = (
            f"用户问题：{question}\n\n"
            f"以下是从知识库检索并扩展的上下文片段（★ 表示向量命中片段）：\n\n"
            f"{context_text}\n\n"
            "请按照要求分析上述片段，输出证据分析与事实摘要。"
        )
        messages: list[BaseMessage] = [
            SystemMessage(content=settings.AGENT_EVIDENCE_SYSTEM_PROMPT),
            HumanMessage(content=evidence_prompt),
        ]

        t_start = time.perf_counter()
        total_chars = 0
        logger.info(
            "[EVIDENCE] 开始证据阅读 | 上下文=%dchar",
            len(context_text),
        )
        try:
            async for chunk in self._evidence_llm.astream(messages):
                token = getattr(chunk, "content", None)
                if not token:
                    continue
                if isinstance(token, list):
                    token = "".join(
                        p.get("text", "") if isinstance(p, dict) else str(p)
                        for p in token
                    )
                total_chars += len(token)
                yield token
        finally:
            elapsed_ms = (time.perf_counter() - t_start) * 1000
            logger.info(
                "[EVIDENCE] 完成 | 耗时=%.1fms 输出=%dchar",
                elapsed_ms,
                total_chars,
            )

    # ------------------------------- 生成 -------------------------------

    def build_messages(
        self,
        history: list[ChatMessageModel],
        context: str,
        question: str,
        *,
        evidence_summary: str = "",
    ) -> list[BaseMessage]:
        messages: list[BaseMessage] = [
            SystemMessage(content=settings.AGENT_SYSTEM_PROMPT),
        ]
        messages.extend(self._history_to_messages(history))
        if context:
            messages.append(
                SystemMessage(content=f"以下是从知识库中检索到的相关片段：\n{context}")
            )
        if evidence_summary:
            messages.append(
                SystemMessage(
                    content=(
                        "以下是对上述知识库片段的证据分析"
                        "（已标注相关性与关键事实，请优先参考）：\n"
                        f"{evidence_summary}"
                    )
                )
            )
        messages.append(HumanMessage(content=question))
        return messages

    async def astream_answer(
        self,
        history: list[ChatMessageModel],
        context: str,
        question: str,
        *,
        evidence_summary: str = "",
    ) -> AsyncIterator[str]:
        """逐 token 流出回答文本，并在终端打印首 token 耗时（TTFT）+ 总耗时。"""
        messages = self.build_messages(history, context, question, evidence_summary=evidence_summary)
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
