"use server";
import { apiClient } from "@/api/apiClient";
import { baseUrl } from "@/api/baseUrl";
import { DocumentType, SearchDocumentQueryType } from "@/models/document";
import axios from "axios";
import { getAuthToken } from "./auth";

/**
 * ドキュメントを検索する
 * @param query - 検索クエリパラメータ
 * @returns 検索結果
 */
export const searchDocument = async (query: SearchDocumentQueryType) => {
  return await apiClient.A002({
    queries: query,
  });
};

/**
 * ドキュメントをアップロードする
 * @param formData - アップロードするファイルを含むFormData
 * @returns アップロード結果
 */
export async function uploadDocument(formData: FormData): Promise<DocumentType> {
  // apiClientを利用したいが、openapi-zod-clientが対応していないのでaxiosをそのまま利用
  const fileName = formData.get("file_name") as string;
  const newFormData = new FormData();
  newFormData.append("file", formData.get("file") as Blob, fileName);
  const FILE_UPLOAD_PATH = "/api/documents/upload";
  const authToken = await getAuthToken();
  const result = await axios.post(baseUrl + FILE_UPLOAD_PATH, newFormData, {
    headers: {
      "Content-Type": "multipart/form-data",
      Authorization: `Bearer ${authToken}`,
    },
  });
  return result.data;
}

/**
 * ドキュメントを削除する
 * @param documentId - 削除対象のドキュメントID
 * @returns 削除結果
 */
export const deleteDocument = async (documentId: string) => {
  return await apiClient.A017(undefined, {
    params: { document_id: documentId },
  });
};
