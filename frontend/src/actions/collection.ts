"use server";
import { apiClient, mockApiClient } from "@/api/apiClient";
import { CreateCollectionRequestType } from "@/models/collection";

/**
 * コレクションを新規作成する
 * @param requestBody - コレクション作成リクエストのパラメータ
 * @returns 作成されたコレクション情報
 */
export const createCollection = async (requestBody: CreateCollectionRequestType) =>
  await apiClient.A003(requestBody);

/**
 * コレクションを更新する
 * @param publicCollectionId - 更新対象のコレクションID
 * @param requestBody - コレクション更新リクエストのパラメータ
 * @returns 更新されたコレクション情報
 */
export const updateCollection = async (
  publicCollectionId: string,
  requestBody: CreateCollectionRequestType
) =>
  await apiClient.A006(requestBody, {
    params: { public_collection_id: publicCollectionId },
  });

/**
 * コレクションの詳細情報を取得する
 * @param publicCollectionId - 取得対象のコレクションID
 * @returns コレクションの詳細情報
 */
export const getCollectionDetail = async (publicCollectionId: string) => {
  return await apiClient.A005({
    params: { public_collection_id: publicCollectionId },
  });
};

/**
 * コレクション一覧を取得する
 * @param limit - 取得件数
 * @returns コレクション一覧
 */
export const getCollectionList = async (limit: number) => {
  return await apiClient.A004({
    queries: {
      limit: limit,
    },
  });
};

/**
 * コレクションに紐づく会話一覧を取得する
 * @param publicCollectionId - コレクションID
 * @returns コレクションに紐づく会話一覧
 */
export const getConversations = async (publicCollectionId: string) => {
  return await apiClient.A008({
    params: { public_collection_id: publicCollectionId },
  });
};

/**
 * コレクション共有リンクを取得する
 * @param publicCollectionId - コレクションID
 * @returns コレクション共有リンク
 */
export const getCollectionShareLink = async (publicCollectionId: string) => {
  return await mockApiClient.A014({
    public_collection_id: publicCollectionId,
  });
};

/**
 * コレクションを削除する
 * @returns 削除結果
 */
export const deleteCollection = async (publicCollectionId: string) => {
  return await mockApiClient.A007(undefined, {
    params: { public_collection_id: publicCollectionId },
  });
};
