import uuid
from datetime import datetime
from nanoid import generate
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class T_Collection(Base):
    __tablename__ = "collections"

    collection_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_collection_id = Column(
        String(11), unique=True, nullable=False, default=lambda: generate(size=11)
    )
    user_id = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    share_id = Column(String(11), unique=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    used_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    collection_documents = relationship(
        "T_CollectionDocument", back_populates="collection", lazy="joined"
    )

    conversations = relationship(
        "T_Conversation", back_populates="collection", lazy="joined"
    )


class T_Document(Base):
    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_type = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    user_id = Column(String(255), nullable=False)
    is_shared = Column(Boolean, nullable=False, default=False)
    summary = Column(Text, nullable=False, default="")
    metadata_info = Column(JSON, nullable=False)
    document_role = Column(String(50), nullable=False, default="normal") #★カスタマイズ開発での追加

    collection_documents = relationship(
        "T_CollectionDocument",
        back_populates="document",
        lazy="joined",
        cascade="all, delete-orphan",
    )


class T_CollectionDocument(Base):
    __tablename__ = "collection_documents"

    collection_id = Column(
        UUID(as_uuid=True), ForeignKey("collections.collection_id"), primary_key=True
    )
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.document_id"), primary_key=True
    )
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    collection = relationship("T_Collection", back_populates="collection_documents")
    document = relationship(
        "T_Document", back_populates="collection_documents", lazy="joined"
    )


class T_Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_conversation_id = Column(String(11), unique=True, nullable=False)
    user_id = Column(String(255), nullable=False)
    collection_id = Column(
        UUID(as_uuid=True), ForeignKey("collections.collection_id"), nullable=False
    )
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    share_id = Column(String(11), unique=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    messages = relationship("T_Message", back_populates="conversation", lazy="joined")
    artifacts = relationship("T_Artifact", back_populates="conversation", lazy="joined")
    collection = relationship("T_Collection", back_populates="conversations")


class T_Message(Base):
    __tablename__ = "messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("conversations.conversation_id"), nullable=False
    )
    sender_type = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    metadata_info = Column(JSON, nullable=False)

    conversation = relationship("T_Conversation", back_populates="messages")
    artifacts = relationship("T_Artifact", back_populates="message")


class T_Artifact(Base):
    __tablename__ = "artifacts"

    artifact_version_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    message_id = Column(
        UUID(as_uuid=True), ForeignKey("messages.message_id"), nullable=False
    )
    conversation_id = Column(
        UUID(as_uuid=True), ForeignKey("conversations.conversation_id"), nullable=False
    )
    artifact_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    conversation = relationship("T_Conversation", back_populates="artifacts")
    message = relationship("T_Message", back_populates="artifacts")
    
    
    
# ★カスタマイズ開発追加
class ReviewTask(Base):
    __tablename__ = "review_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    
    # pending / running / completed / failed
    status = Column(String(50), nullable=False, default="pending")

    # 何個のノウハウルールを処理対象にしたか
    total_rules = Column(Integer, nullable=False, default=0)

    # 何個のルールを処理済みか
    completed_rules = Column(Integer, nullable=False, default=0)

    # 最終的な要約。最初は未使用でもOK
    summary = Column(Text, nullable=True)

    # エラー時のメッセージ
    error_message = Column(Text, nullable=True)
    
     # レビュー対象ドキュメントID一覧
    # PostgreSQL JSON/JSONB を想定
    input_doc_ids = Column(JSON, nullable=False, default=list)

    # ノウハウドキュメントID一覧
    knowhow_doc_ids = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
    )

    results = relationship(
        "ReviewResult",
        back_populates="task",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    
class ReviewResult(Base):
    __tablename__ = "review_results"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)

    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("review_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # どのノウハウルールに基づく指摘か
    rule_id = Column(String(255), nullable=False, index=True)

    # ng / unknown
    status = Column(String(50), nullable=False)

    # low / medium / high
    severity = Column(String(50), nullable=False)

    # 指摘対象。Signal名、PDU名、章番号など
    target = Column(String(500), nullable=True)

    # 指摘内容
    finding = Column(Text, nullable=False)

    # 判断理由
    reason = Column(Text, nullable=False)

    # 修正案
    suggestion = Column(Text, nullable=False)

    # 根拠情報
    evidences = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    task = relationship(
        "ReviewTask",
        back_populates="results",
    )
    
    human_status = Column(String(50), nullable=True)
    human_comment = Column(Text, nullable=True)
    corrected_finding = Column(Text, nullable=True)
    corrected_reason = Column(Text, nullable=True)
    corrected_suggestion = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    
    
    
    
