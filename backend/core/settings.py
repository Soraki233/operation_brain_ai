from pydantic_settings import BaseSettings
from pydantic import computed_field


# 环境设置类，用于获取当前环境
class EnvSettings(BaseSettings):
    env: str = "dev"

    class Config:
        env_file = ".env.current"


class Settings(BaseSettings):
    # 数据库配置
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    # 阿里云配置
    ALIYUN_ACCESS_KEY: str
    ALIYUN_SECRET_KEY: str
    SMS_SIGN_NAME: str
    SMS_TEMPLATE_CODE: str

    # Redis配置
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str
    REDIS_DB: int = 0
    REDIS_KEY_PREFIX: str
    REDIS_DEFAULT_TTL: int

    # Token相关
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int

    # RAG / Qwen
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_CHAT_MODEL: str = "qwen-plus"
    QWEN_EMBEDDING_MODEL: str = "text-embedding-v4"
    EMBEDDING_DIM: int = 1024

    # 文件
    KNOWLEDGE_UPLOAD_DIR: str = "storage/knowledge"
    KNOWLEDGE_MAX_FILE_SIZE_MB: int = 50

    # 切块
    KNOWLEDGE_CHUNK_SIZE: int = 800
    KNOWLEDGE_CHUNK_OVERLAP: int = 120

    # 检索
    KNOWLEDGE_RETRIEVE_TOP_K: int = 5

    # Agent（RAG 问答）
    AGENT_SYSTEM_PROMPT: str = (
        "你是潜江首创电厂的运行AI助手，你的名字叫：运行智脑，专注回答垃圾焚烧发电厂的运行方面的问题。"
        "运行参数、运行指标、运行工况等相关问题。\n"
        "回答要求：\n"
        "1. 优先参考随后提供的【知识库片段】内容；\n"
        "2. 引用的信息需要准确、可核对，能溯源的用 [#序号] 标注出处；\n"
        "3. 若知识库与自身知识均无法确认答案，请直接说明不知道，不要臆造；\n"
        "4. 输出使用简洁的中文 Markdown，结构清晰（分点、代码块等）。\n"
        "5. 回答问题可以结合电厂的实际情况，给出合理的建议。\n"
        "6. 可以根据网络搜索到的信息，给出合理的建议。\n"
        " 回答问题时请遵循以下流程：\n"
        "1. 先使用检索工具找到可能相关的知识片段\n"
        "2. 如果片段信息不足以支持准确回答，继续阅读该片段的上下文、相邻段落或所属章节\n"
        "3. 优先根据完整语义而不是关键词字面匹配作出判断\n"
        "4. 只有在阅读到足够证据后再回答\n"
        "5. 如果检索结果相关但证据仍不足，明确说明“当前检索到的信息不足以确认答案”\n"
        "6. 不要只因为出现了相关关键词就草率下结论"
    )
    AGENT_TEMPERATURE: float = 0.3
    AGENT_MAX_TOKENS: int = 1024
    # pgvector 用的是 cosine distance，范围 0~2：
    # - 0.0 ~ 0.35 ：高度相关
    # - 0.35 ~ 0.55：相关，可作弱参考
    # - 0.55 以上  ：基本无关，应丢弃
    # 过宽会把无关的 CSV/表格片段也带进上下文，导致模型回答里出现无关引用。
    AGENT_RAG_SCORE_MAX_DISTANCE: float = 0.45
    # 命中 chunk 后向前/后各扩读的相邻 chunk 数（0 = 不扩展）
    AGENT_RAG_CONTEXT_WINDOW: int = 2

    # 证据阅读（RAG 第三步）
    # 设为 False 退化为原有三步流程（检索 → 扩展 → 回答）
    AGENT_EVIDENCE_READ_ENABLED: bool = True
    AGENT_EVIDENCE_MAX_TOKENS: int = 1200
    AGENT_EVIDENCE_SYSTEM_PROMPT: str = (
        "你是一个专业的证据阅读器。你的任务是对知识库检索片段进行分析，"
        "判断其与用户问题的相关性，并提炼关键事实。\n\n"
        "输出格式要求：\n"
        "1. 逐一分析每个片段（用★标记的是向量命中片段，其余为扩展上下文）：\n"
        "   - 相关性：高度相关 / 间接相关 / 无关\n"
        "   - 关键信息：一句话摘要（无关片段可省略）\n"
        "2. 最后输出【事实摘要】：按重要性排列从片段中提取的关键事实，"
        "用于支撑对用户问题的回答。\n\n"
        "注意：\n"
        "- 只做分析，不要直接回答用户问题\n"
        "- 保持客观，不要添加片段中没有的信息\n"
        "- 若所有片段都无关，【事实摘要】写'当前知识库片段与问题无关'"
    )

    # 文档结构分析（切分前）
    # 为 False 时退化为 RecursiveCharacterTextSplitter
    STRUCTURE_ANALYZER_ENABLED: bool = True
    # 单次 LLM 调用的输入长度上限，超过后自动按段落粗切多次分析
    STRUCTURE_ANALYZER_MAX_INPUT_CHARS: int = 12000
    # LLM 输出上限（JSON 模式下用于容纳结构化输出）
    STRUCTURE_ANALYZER_MAX_TOKENS: int = 4096
    STRUCTURE_ANALYZER_SYSTEM_PROMPT: str = (
        "你是一个知识库文档结构分析助手。\n"
        "你的任务是分析输入的文档内容，并识别其结构边界，以便后续进行高质量切割。\n\n"
        "【识别目标】\n"
        "请识别以下结构：\n"
        "1. 文档标题\n"
        "2. 一级章节\n"
        "3. 二级章节\n"
        "4. 条款编号\n"
        "5. 步骤列表\n"
        "6. 注意事项 / 警告 / 禁止项\n"
        "7. 表格内容\n"
        "8. 普通说明段落\n\n"
        "【输出要求】\n"
        "请**严格**以 JSON 对象格式输出，结构如下：\n"
        '{"units": [\n'
        '  {"type": "<结构类型>", "title": "<标题或条款名>", '
        '"content": "<正文内容>", "level": <层级 0-5>, '
        '"keywords": ["<关键词1>", "<关键词2>"]}\n'
        "]}\n\n"
        "type 取值建议：doc_title / heading_1 / heading_2 / heading_3 / "
        "clause / steps / notice / warning / forbidden / table / paragraph\n\n"
        "【约束】\n"
        "1. 不要按固定长度切割\n"
        "2. 优先保持语义完整：条件、操作、结果尽量保留在同一结构单元中\n"
        "3. 步骤列表不要拆散\n"
        "4. 表格单独标记为 table，content 保留原始表格文本\n"
        "5. 只输出 JSON，不要输出 Markdown 代码块包装、不要任何解释性文字\n"
        "6. 无标题的段落 title 字段可写为空字符串 '' 或简短摘要"
    )

    # 线程历史压缩
    THREAD_SUMMARY_TRIGGER_MSG_COUNT: int = 20
    THREAD_SUMMARY_TRIGGER_TOKEN_EST: int = 6000
    THREAD_KEEP_RECENT_MSGS: int = 8

    # 上下文压缩
    MAX_CONTEXT_CHARS: int = 12000
    CONTEXT_GROUP_CHARS: int = 3500

    # 构建异步数据库 URL
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def VECTOR_DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    class Config:
        # 让环境变量文件名根据环境变量动态加载
        env_file = f".env.{EnvSettings().env}"
        extra = "ignore"


def get_settings():
    return Settings()


env_settings = EnvSettings()
settings = get_settings()
