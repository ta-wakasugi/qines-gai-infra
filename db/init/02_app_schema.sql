\connect qinesgai qinesgai

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


CREATE TABLE collections (
    collection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    public_collection_id VARCHAR(11) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    share_id VARCHAR(11) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_collections_public_collection_id ON collections (public_collection_id);
CREATE INDEX idx_collections_share_id ON collections (share_id);



CREATE TABLE documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    file_type VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255) NOT NULL, 
    is_shared BOOLEAN NOT NULL DEFAULT FALSE,
    summary TEXT NOT NULL DEFAULT '',
    metadata_info JSONB NOT NULL
);



CREATE TABLE collection_documents (
    collection_id UUID REFERENCES collections(collection_id),
    document_id UUID REFERENCES documents(document_id),
    PRIMARY KEY (collection_id, document_id),
    position INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);



CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    public_conversation_id VARCHAR(11) UNIQUE NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    collection_id UUID NOT NULL REFERENCES collections(collection_id),
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    share_id VARCHAR(11) UNIQUE, 
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_conversations_public_conversation_id ON conversations (public_conversation_id);
CREATE INDEX idx_conversations_share_id ON conversations (share_id);



CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id),
    sender_type VARCHAR(10) NOT NULL CHECK (sender_type IN ('user', 'ai')),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata_info JSONB NOT NULL
);

CREATE INDEX idx_messages_conversation_id ON messages (conversation_id);



CREATE TABLE artifacts (
    artifact_version_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES messages(message_id),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id),
    artifact_id UUID NOT NULL,
    title TEXT NOT NULL,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (conversation_id, artifact_id, version)
);

CREATE INDEX idx_artifacts_conversation_id ON artifacts (conversation_id);
