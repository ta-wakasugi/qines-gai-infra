import uuid

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
