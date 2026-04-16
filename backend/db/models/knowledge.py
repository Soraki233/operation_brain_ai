from sqlalchemy import Column, String, Integer, BigInteger, SmallInteger, Text

from db.session import BaseModel


class KnowledgeBase(BaseModel):
    __tablename__ = "knowledge_base"

    name = Column(String(100), nullable=False, index=True, comment="知识库名称")
    scope = Column(String(20), nullable=False, index=True, comment="personal/shared")

    # personal 时为用户ID，shared 时为空
    owner_user_id = Column(
        String(32), nullable=True, index=True, comment="知识库归属用户ID"
    )
    creator_user_id = Column(String(32), nullable=False, index=True, comment="创建人ID")

    is_active = Column(
        SmallInteger,
        nullable=False,
        default=1,
        comment="是否启用(1启用,0停用)",
    )


class KnowledgeFolder(BaseModel):
    __tablename__ = "knowledge_folder"

    kb_id = Column(String(32), nullable=False, index=True, comment="知识库ID")
    parent_id = Column(
        String(32), nullable=True, index=True, comment="父文件夹ID，当前可先不使用"
    )
    name = Column(String(100), nullable=False, index=True, comment="文件夹名称")
    creator_user_id = Column(String(32), nullable=False, index=True, comment="创建人ID")
    sort_order = Column(Integer, nullable=False, default=0, comment="排序")
    is_active = Column(SmallInteger, nullable=False, default=1, comment="是否启用")


class KnowledgeFile(BaseModel):
    __tablename__ = "knowledge_file"

    kb_id = Column(String(32), nullable=False, index=True, comment="知识库ID")
    folder_id = Column(
        String(32), nullable=True, index=True, comment="文件夹ID，可空表示知识库根目录"
    )
    file_name = Column(String(255), nullable=False, index=True, comment="显示文件名")
    file_ext = Column(String(20), nullable=False, comment="文件扩展名")
    mime_type = Column(String(100), nullable=True, comment="MIME类型")
    file_size = Column(BigInteger, nullable=False, default=0, comment="文件大小")
    storage_path = Column(String(500), nullable=False, comment="本地存储路径")

    parse_status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="pending/processing/success/failed",
    )
    chunk_count = Column(Integer, nullable=False, default=0, comment="切块数")
    uploaded_by = Column(String(32), nullable=False, index=True, comment="上传人ID")
    error_message = Column(Text, nullable=True, comment="失败原因")
