"""LLM 结构化文档切分。

把整篇文档交给 LLM（Qwen / DashScope），让模型按语义边界拆成
结构单元列表（章节 / 条款 / 步骤 / 表格 / 段落 …），每个单元自带
title / type / level / keywords，便于下游写入向量库 metadata、
提升检索召回的精准度。

失败策略：任何异常（网络、JSON 非法、空结果）都抛 StructureAnalyzeError，
调用方自行决定是否退化到 RecursiveCharacterTextSplitter。
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from core.settings import settings

logger = logging.getLogger(__name__)


class StructureAnalyzeError(Exception):
    """结构分析失败（调用方应退化到旧切分策略）。"""


@dataclass
class StructureUnit:
    """LLM 解析出的一个结构单元。"""

    type: str = "paragraph"
    title: str = ""
    content: str = ""
    level: int = 0
    keywords: List[str] = field(default_factory=list)


class StructureAnalyzer:
    # 单段 LLM 调用硬超时（秒）。DashScope qwen-plus JSON 长输出偶发
    # 响应极慢甚至挂起，超时后直接抛异常让上游 fallback，避免卡住 ingest。
    _CALL_TIMEOUT_SECONDS: int = 90
    # httpx 层面重试次数（langchain_openai 内部重试），超过后抛出
    _MAX_RETRIES: int = 1

    def __init__(self) -> None:
        # 独立的 LLM 实例：temperature=0 保证输出稳定。
        # 说明：不开 response_format=json_object —— DashScope 兼容层对该参数
        # 在 qwen-plus 下偶发返回 pending/挂起，反而更不稳定。prompt 里已经
        # 明确要求纯 JSON 输出，_parse_json 也有兜底解析，足够应对。
        self._llm = ChatOpenAI(
            model=settings.QWEN_CHAT_MODEL,
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
            temperature=0,
            max_tokens=settings.STRUCTURE_ANALYZER_MAX_TOKENS,
            timeout=self._CALL_TIMEOUT_SECONDS,
            max_retries=self._MAX_RETRIES,
        )

    # --------------------------- 公开接口 ---------------------------

    def analyze(self, text: str) -> List[StructureUnit]:
        """把整篇文档解析成结构单元列表。

        文本过长时按段落粗切成若干块分别分析，然后合并。
        """
        text = (text or "").strip()
        if not text:
            raise StructureAnalyzeError("空文本")

        max_input = settings.STRUCTURE_ANALYZER_MAX_INPUT_CHARS
        blocks = self._split_for_analysis(text, max_chars=max_input)

        units: List[StructureUnit] = []
        t_start = time.perf_counter()
        for i, block in enumerate(blocks, start=1):
            try:
                sub_units = self._analyze_block(block)
            except StructureAnalyzeError:
                raise
            except Exception as e:  # noqa: BLE001
                logger.exception(
                    "[STRUCTURE] 第 %d/%d 段分析失败 err=%s", i, len(blocks), e
                )
                raise StructureAnalyzeError(str(e)) from e
            logger.info(
                "[STRUCTURE] 段落 %d/%d 解析完成 输入=%dchar 单元=%d",
                i,
                len(blocks),
                len(block),
                len(sub_units),
            )
            units.extend(sub_units)

        elapsed_ms = (time.perf_counter() - t_start) * 1000
        logger.info(
            "[STRUCTURE] 全文分析完成 | 段数=%d 单元=%d 耗时=%.1fms",
            len(blocks),
            len(units),
            elapsed_ms,
        )

        if not units:
            raise StructureAnalyzeError("LLM 返回空单元")

        return units

    # --------------------------- 内部方法 ---------------------------

    @staticmethod
    def _split_for_analysis(text: str, *, max_chars: int) -> List[str]:
        """长文本按 \\n\\n / 换行粗切成 ≤ max_chars 的大块，
        仅保证不破坏段落，不做语义切分（这由 LLM 自己完成）。
        """
        if len(text) <= max_chars:
            return [text]

        # 先按空行切；不够细再按单个换行
        paragraphs = [p for p in re.split(r"\n{2,}", text) if p.strip()]
        blocks: List[str] = []
        buf = ""
        for p in paragraphs:
            candidate = p if not buf else f"{buf}\n\n{p}"
            if len(candidate) <= max_chars:
                buf = candidate
                continue
            # buf 先收口，然后处理当前段
            if buf:
                blocks.append(buf)
                buf = ""
            if len(p) <= max_chars:
                buf = p
            else:
                # 单段超长：按换行 / 硬切
                blocks.extend(StructureAnalyzer._hard_split(p, max_chars))
        if buf:
            blocks.append(buf)
        return blocks

    @staticmethod
    def _hard_split(text: str, max_chars: int) -> List[str]:
        """超长段落的兜底切法：优先按 \\n 切，仍超长则按定长切。"""
        parts: List[str] = []
        buf = ""
        for line in text.split("\n"):
            candidate = line if not buf else f"{buf}\n{line}"
            if len(candidate) <= max_chars:
                buf = candidate
                continue
            if buf:
                parts.append(buf)
                buf = ""
            if len(line) <= max_chars:
                buf = line
            else:
                for i in range(0, len(line), max_chars):
                    parts.append(line[i : i + max_chars])
        if buf:
            parts.append(buf)
        return parts

    def _analyze_block(self, block: str) -> List[StructureUnit]:
        """调用 LLM 分析单个块，返回结构单元列表。"""
        messages = [
            SystemMessage(content=settings.STRUCTURE_ANALYZER_SYSTEM_PROMPT),
            HumanMessage(content=block),
        ]
        t0 = time.perf_counter()
        logger.info(
            "[STRUCTURE] 调用 LLM | 模型=%s 输入=%dchar timeout=%ds",
            settings.QWEN_CHAT_MODEL,
            len(block),
            self._CALL_TIMEOUT_SECONDS,
        )
        resp = self._llm.invoke(messages)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        raw = getattr(resp, "content", "")
        if isinstance(raw, list):
            raw = "".join(
                p.get("text", "") if isinstance(p, dict) else str(p) for p in raw
            )
        raw = (raw or "").strip()
        logger.info(
            "[STRUCTURE] LLM 返回 | 耗时=%.1fms 输出=%dchar", elapsed_ms, len(raw)
        )
        if not raw:
            raise StructureAnalyzeError("LLM 返回空串")

        data = self._parse_json(raw)
        items = data.get("units")
        if not isinstance(items, list):
            raise StructureAnalyzeError("LLM 输出缺少 units 列表")

        units: List[StructureUnit] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            content = str(it.get("content") or "").strip()
            if not content:
                continue
            title = str(it.get("title") or "").strip()
            type_ = str(it.get("type") or "paragraph").strip() or "paragraph"
            level_raw = it.get("level", 0)
            try:
                level = int(level_raw)
            except (TypeError, ValueError):
                level = 0
            kws_raw = it.get("keywords") or []
            if isinstance(kws_raw, list):
                keywords = [str(k).strip() for k in kws_raw if str(k).strip()]
            else:
                keywords = [str(kws_raw).strip()] if str(kws_raw).strip() else []
            units.append(
                StructureUnit(
                    type=type_,
                    title=title,
                    content=content,
                    level=level,
                    keywords=keywords,
                )
            )
        return units

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """容错解析：直接 loads → 剥 ```json 包裹 → 提取花括号片段。"""
        try:
            return json.loads(raw)
        except Exception:
            pass

        # 去掉 ```json ... ``` 代码块
        fenced = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
        if fenced:
            try:
                return json.loads(fenced.group(1).strip())
            except Exception:
                pass

        # 抓第一个 {...} 片段
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass

        raise StructureAnalyzeError("LLM 输出无法解析为 JSON")
