"use server";
import { apiClient } from "@/api/apiClient";
import { AddDocumentRequestType } from "@/models/artifact";
import { UpdateDocumentRequestType } from "@/models/artifact";

type DownloadArtifactParams = {
  artifact_id: string;
  version: number;
  format: string;
};

/**
 * 成果物をダウンロードする
 * @param params - ダウンロードパラメータ
 * @returns ダウンロードレスポンス
 */
export const downloadArtifact = async (params: DownloadArtifactParams) => {
  return await apiClient.A020(undefined, { queries: params });
};

/**
 * コレクションに成果物を新規追加する
 * @param requestBody - 成果物新規追加リクエストデータ
 * @returns 新規追加結果
 */
export const addArtifact = async (requestBody: AddDocumentRequestType) =>
  await apiClient.A021(requestBody);

/**
 * コレクション内の成果物を編集し更新する
 * @param requestBody - 成果物更新リクエストデータ
 * @returns 更新結果
 */
export const updateArtifact = async (requestBody: UpdateDocumentRequestType) =>
  await apiClient.A022(requestBody);
