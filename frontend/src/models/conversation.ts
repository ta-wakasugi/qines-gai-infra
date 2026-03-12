import { schemas } from "@/api/openapiClient";
import { z } from "zod";

export type ArtifactType = z.infer<typeof schemas.Artifact>;
export type ConversationBaseType = z.infer<typeof schemas.ConversationBase>;
export type GetConversationRequestType = { public_conversation_id: string };
export type ContextType = z.infer<typeof schemas.Context>;
export type ChatRequestType = z.infer<typeof schemas.ChatCompletionsRequest>;
export type ChatRequestBaseType = z.infer<typeof schemas.ChatRequestBase>;
export type MessageType = z.infer<typeof schemas.Message>;
export type MessageMetaDataType = z.infer<typeof schemas.MessageMetadata>;
export type RecommendDocumentType = MessageMetaDataType["recommended_documents"];
export type StreamChatType = z.infer<typeof schemas.StreamChat>;
export type SharedConversationType = z.infer<typeof schemas.SharedConversation>;
