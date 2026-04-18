from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
)

from service.vector_store_service import VectorStoreService
from core.settings import settings


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
            # 避开 UnstructuredExcelLoader（其 xlsx 分支依赖 networkx / unstructured 全家桶），
            # 直接用 pandas 按 sheet 读取。不用 CSV：对 LLM 来说 ",,,," 这种空列
            # 几乎没有语义，改成 "字段=值 | 字段=值" 的记录格式，召回片段能直接
            # 被模型理解，表头也会被切片逻辑自动复用到每个 chunk。
            engine = "openpyxl" if suffix == ".xlsx" else "xlrd"
            sheet_names = pd.ExcelFile(str(path), engine=engine).sheet_names
            docs = []
            for sheet_name in sheet_names:
                df = self._read_excel_sheet_smart(
                    str(path), sheet_name=sheet_name, engine=engine
                )
                df = self._clean_excel_dataframe(df)
                if df.empty:
                    continue
                text = self._dataframe_to_records_text(df, sheet_name=sheet_name)
                if not text.strip():
                    continue
                docs.append(
                    Document(
                        page_content=text,
                        metadata={"source": str(path), "sheet": sheet_name},
                    )
                )
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
            chunk_size=settings.KNOWLEDGE_CHUNK_SIZE,
            chunk_overlap=settings.KNOWLEDGE_CHUNK_OVERLAP,
            separators=[
                "\n\n",
                "\n",
                "。",
                "！",
                "？",
                "；",
                "，",
                " ",
                "",
                ",",
                "\t",
                "\r",
                "\s",
            ],
        )

        chunks: List[Document] = []
        non_excel_docs: List[Document] = []
        for doc in docs:
            metadata = dict(doc.metadata or {})
            metadata.update({"kb_id": kb_id, "file_id": file_id})
            normalized = Document(page_content=doc.page_content, metadata=metadata)
            # Excel sheet 的内容是 CSV 文本，必须按行切并保留表头，
            # 否则单行被切到一半 / 后续 chunk 没表头，召回的片段模型完全读不懂。
            if metadata.get("sheet"):
                chunks.extend(
                    self._split_csv_document(
                        normalized,
                        max_chars=settings.KNOWLEDGE_CHUNK_SIZE,
                    )
                )
            else:
                non_excel_docs.append(normalized)

        if non_excel_docs:
            chunks.extend(splitter.split_documents(non_excel_docs))

        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx

        return chunks

    # 被视为表头的前缀：遇到以这些前缀开头的行，都会被视为需要复用到每个 chunk 的"表头"。
    _HEADER_LINE_PREFIXES = ("工作表：", "字段：")

    @staticmethod
    def _split_csv_document(doc: Document, *, max_chars: int) -> List[Document]:
        """按行切分表格 Document，保证：
        1. 不会把一行数据切到中间；
        2. 每个 chunk 都重复带上表头行（"工作表：..." / "字段：..."），
           让召回片段是"表头 + 若干完整数据行"，模型能直接读懂字段含义。
        """
        text = doc.page_content or ""
        lines = text.split("\n")
        while lines and not lines[-1].strip():
            lines.pop()

        if not lines:
            return []
        if len(lines) == 1:
            return [doc]

        # 把开头连续的"表头行"识别出来；兼容无前缀的情况（退化成首行当表头）
        header_lines: list[str] = []
        idx = 0
        while idx < len(lines) and lines[idx].startswith(
            KnowledgeIngestService._HEADER_LINE_PREFIXES
        ):
            header_lines.append(lines[idx])
            idx += 1
        if not header_lines:
            header_lines = [lines[0]]
            idx = 1

        header_block = "\n".join(header_lines)
        data_lines = lines[idx:]
        if not data_lines:
            return [doc]

        header_len = len(header_block) + 1
        # 表头本身过长时放弃复用表头，至少不切断行
        carry_header = header_len < max(max_chars // 2, 256)

        chunks: List[Document] = []
        buffer: List[str] = []
        buffer_len = header_len if carry_header else 0
        start_row = 0

        def flush(end_row_exclusive: int) -> None:
            if not buffer:
                return
            body = "\n".join(buffer)
            content = f"{header_block}\n{body}" if carry_header else body
            metadata = dict(doc.metadata or {})
            metadata["row_range"] = [start_row, end_row_exclusive - 1]
            chunks.append(Document(page_content=content, metadata=metadata))

        for i, line in enumerate(data_lines):
            line_len = len(line) + 1
            if buffer and (buffer_len + line_len) > max_chars:
                flush(i)
                buffer = []
                buffer_len = header_len if carry_header else 0
                start_row = i
            buffer.append(line)
            buffer_len += line_len

        flush(len(data_lines))

        return chunks or [doc]

    # DashScope text-embedding-v3/v4 单次请求最多 10 条文本，超过会直接 4xx。
    # 而 langchain_community.DashScopeEmbeddings.embed_documents 不会主动分批，
    # 因此我们在调用 add_documents 之前手工切片。
    EMBEDDING_BATCH_SIZE: int = 10

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

        for start in range(0, len(chunks), self.EMBEDDING_BATCH_SIZE):
            batch_docs = chunks[start : start + self.EMBEDDING_BATCH_SIZE]
            batch_ids = ids[start : start + self.EMBEDDING_BATCH_SIZE]
            try:
                self.vector_store.add_documents(documents=batch_docs, ids=batch_ids)
            except Exception as exc:
                raise self._wrap_embedding_error(exc, batch_index=start) from exc

        return {
            "chunk_count": len(chunks),
            "message": "文件入库成功",
        }

    @staticmethod
    def _wrap_embedding_error(exc: Exception, *, batch_index: int) -> Exception:
        """DashScope 的 HTTPError 会因为 response 是 dict-like 而被
        ``requests.exceptions.HTTPError.__init__`` 二次抛出 ``KeyError('request')``，
        把真正的 status_code/code/message 完全吞掉。这里尽量还原可读信息。
        """
        msg = str(exc) if str(exc) else exc.__class__.__name__

        # 典型表现：KeyError: 'request'  ←  来自 dashscope_response.__getattr__
        if isinstance(exc, KeyError) and "request" in msg:
            msg = (
                "DashScope embedding 请求失败（疑似单批文本数 / 单文本 token 超限，"
                "或 API Key/网络异常）。已自动按 10 条/批切分仍报错，请检查 API "
                "配额或缩小 KNOWLEDGE_CHUNK_SIZE。"
            )

        return RuntimeError(f"[batch_offset={batch_index}] {msg}")

    def delete_file_vectors(self, *, file_id: str, chunk_count: int) -> None:
        if chunk_count <= 0:
            return
        ids = [f"{file_id}:{i}" for i in range(chunk_count)]
        self.vector_store.delete(ids=ids)

    @staticmethod
    def _read_excel_sheet_smart(
        file_path: str, *, sheet_name: str, engine: str
    ) -> pd.DataFrame:
        """读取单个 sheet，并自动识别多级表头：
        - 规则：扫描前若干行，第一个"多数单元格是数字"的行判为数据行；
          它之前的行都算表头，多级合并成 "主标题-子标题" 这种可读列名。
        - 这样处理图里那种 "日期/时间/博总线(正向有功总/反向有功总)/电量(...)" 的
          合并表头，就不会把 "正向有功总" 这些子标题错误当成数据。
        """
        probe = pd.read_excel(
            file_path, sheet_name=sheet_name, engine=engine, header=None, nrows=12
        )
        header_depth = KnowledgeIngestService._detect_header_depth(probe)

        if header_depth <= 1:
            return pd.read_excel(
                file_path, sheet_name=sheet_name, engine=engine, header=0
            )

        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            engine=engine,
            header=list(range(header_depth)),
        )
        df.columns = [
            KnowledgeIngestService._flatten_header(col) for col in df.columns
        ]
        return df

    @staticmethod
    def _detect_header_depth(probe: pd.DataFrame) -> int:
        """前若干行里，第一个 "数字占比 ≥ 50%" 的行 = 表头深度；否则默认 1。"""
        if probe is None or probe.empty:
            return 1
        for i in range(min(6, len(probe))):
            row = probe.iloc[i]
            non_null = [v for v in row if pd.notna(v)]
            if not non_null:
                continue
            numeric = sum(
                1
                for v in non_null
                if isinstance(v, (int, float)) and not isinstance(v, bool)
            )
            if numeric / len(non_null) >= 0.5:
                return max(1, i)
        return 1

    @staticmethod
    def _flatten_header(col) -> str:
        """把多级表头的 tuple 合并成 "A-B-C"，过滤 NaN / Unnamed / 重复。"""
        if isinstance(col, tuple):
            parts: list[str] = []
            for c in col:
                s = (
                    ""
                    if c is None or (isinstance(c, float) and pd.isna(c))
                    else str(c).strip()
                )
                if not s or s.startswith("Unnamed:"):
                    continue
                if s in parts:
                    continue
                parts.append(s)
            return "-".join(parts)
        s = str(col).strip()
        return "" if s.startswith("Unnamed:") else s

    @staticmethod
    def _clean_excel_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """清洗 pandas 读取的 DataFrame：
        1. 丢弃整列为空 / 列名全空的列；
        2. 丢弃整行为空的行；
        3. **保留原始类型**（日期仍然是 datetime），不强转字符串，否则日期会被
           Excel 序列号（如 44927）污染。
        """
        if df is None or df.empty:
            return df

        df = df.copy()
        # 只规范化字符串形式的 'nan' / 'NaN'，不 fillna（否则 datetime 列会崩）
        df = df.replace({"nan": None, "NaN": None})

        keep_idx: list[int] = []
        for i in range(df.shape[1]):
            col_name = str(df.columns[i]).strip()
            col_values = df.iloc[:, i]
            is_all_empty = col_values.isna().all() or (
                col_values.astype(str).str.strip() == ""
            ).all()
            if is_all_empty and (not col_name or col_name.startswith("Unnamed:")):
                continue
            if is_all_empty and not col_name:
                continue
            keep_idx.append(i)

        if not keep_idx:
            return df.iloc[0:0]
        df = df.iloc[:, keep_idx]

        df.columns = [
            "" if str(col).startswith("Unnamed:") else str(col).strip()
            for col in df.columns
        ]

        if not df.empty:
            row_is_empty = df.apply(
                lambda row: all(
                    (v is None)
                    or (isinstance(v, float) and pd.isna(v))
                    or (str(v).strip() == "")
                    for v in row
                ),
                axis=1,
            )
            df = df.loc[~row_is_empty]

        return df

    @staticmethod
    def _dataframe_to_records_text(df: pd.DataFrame, *, sheet_name: str) -> str:
        """把 DataFrame 转成面向 LLM 的"记录式"文本：

            工作表：2024
            字段：日期、时间、博总线-正向有功总、博总线-反向有功总、...
            行1：日期=2024-01-01 | 时间=08:00 | 博总线-正向有功总=8608.70 | ...
            行2：日期=2024-01-01 | 时间=16:00 | ...

        - 日期列格式化，不再出现 44927 这种 Excel 序列号；
        - 空值不写成 "key="，降噪；
        - 首行 "字段：..." 会被 _split_csv_document 当表头复用到每个 chunk。
        """
        if df is None or df.empty:
            return ""

        df = df.copy()

        for col in df.columns:
            s = df[col]
            if pd.api.types.is_datetime64_any_dtype(s):
                dt = pd.to_datetime(s, errors="coerce")
                has_time = bool(
                    (
                        (dt.dt.hour.fillna(0) != 0)
                        | (dt.dt.minute.fillna(0) != 0)
                        | (dt.dt.second.fillna(0) != 0)
                    ).any()
                )
                fmt = "%Y-%m-%d %H:%M:%S" if has_time else "%Y-%m-%d"
                df[col] = dt.dt.strftime(fmt)

        cols = [str(c).strip() for c in df.columns]
        non_empty_cols = [c for c in cols if c]

        lines: list[str] = [f"工作表：{sheet_name}"]
        if non_empty_cols:
            lines.append("字段：" + "、".join(non_empty_cols))

        for i, row in enumerate(df.itertuples(index=False, name=None), start=1):
            parts: list[str] = []
            for col, val in zip(cols, row):
                if not col:
                    continue
                if val is None:
                    continue
                if isinstance(val, float) and pd.isna(val):
                    continue
                # 去掉 5566.780000 这种拖尾 0
                if isinstance(val, float):
                    if val.is_integer():
                        val_str = str(int(val))
                    else:
                        val_str = ("%.6f" % val).rstrip("0").rstrip(".")
                else:
                    val_str = str(val).strip()
                if not val_str:
                    continue
                parts.append(f"{col}={val_str}")
            if parts:
                lines.append(f"行{i}：" + " | ".join(parts))

        # 只有工作表/字段两行、没数据行 => 视为空
        if len(lines) <= 2:
            return ""
        return "\n".join(lines)
