"use server";

import { apiClient, mockApiClient } from "@/api/apiClient";
import { schemas } from "@/api/openapiClient";
import { CollectionDetailType } from "@/models/collection";
import { ChatRequestBaseType, GetConversationRequestType } from "@/models/conversation";

/**
 * 会話履歴を取得する
 * @param params - 会話履歴取得のためのパラメータ
 * @returns 会話履歴
 */
export const getConversation = async (params: GetConversationRequestType) =>
  await apiClient.A009({
    params,
  });

/**
 * まずは聞いてみるを用いてチャットを開始する
 * @param requestBody - チャット開始リクエストのパラメータ
 * @returns コレクション詳細情報
 */
export const postChatStart = async (
  requestBody: ChatRequestBaseType
): Promise<CollectionDetailType> => {
  const response = await apiClient.A012(requestBody);
  return schemas.CollectionDetail.parse(response);
};

/**
 * 会話の共有リンクを取得する
 * @param conversationId - 会話ID
 * @returns コレクション共有リンク
 */
export const getConversationShareLink = async (conversationId: string) => {
  return await mockApiClient.A015({
    public_conversation_id: conversationId,
  });
};

/**
 * 会話を削除する
 * @param conversationId - 会話ID
 */
export const deleteConversation = async (conversationId: string) => {
  return await mockApiClient.A010(undefined, {
    params: { public_conversation_id: conversationId },
  });
};
