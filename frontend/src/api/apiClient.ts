import { getAuthToken } from "@/actions/auth";
import { createApiClient } from "@/api/openapiClient";
import { InternalAxiosRequestConfig, AxiosError } from "axios";
import { baseUrl, mockBaseUrl } from "./baseUrl";
import { redirect } from "next/navigation";

/**
 * リクエストにAuthorizationヘッダーを追加するインターセプター
 * @param config - Axiosリクエスト設定
 * @returns 認証トークンが付与された設定
 */
const addAuthorizationHeader = async (config: InternalAxiosRequestConfig) => {
  const token = await getAuthToken();

  if (token) {
    config.headers = config.headers || {};
    config.headers["Authorization"] = `Bearer ${token}`;
  }

  return config;
};

/** モック用APIクライアントインスタンス（Prism用） */
export const mockApiClient = createApiClient(mockBaseUrl);

/** 本番用APIクライアントインスタンス（バックエンド用） */
export const apiClient = createApiClient(baseUrl);

// backendのAPIを叩く際にAuthorizationヘッダにトークンを付与する
mockApiClient.axios.interceptors.request.use(addAuthorizationHeader);
apiClient.axios.interceptors.request.use(addAuthorizationHeader);

// レスポンスインターセプター: 401エラー時にログイン画面にリダイレクト
const handleUnauthorized = (error: AxiosError) => {
  if (error.response?.status === 401) {
    redirect("/login");
  }
  return Promise.reject(error);
};

mockApiClient.axios.interceptors.response.use(undefined, handleUnauthorized);

apiClient.axios.interceptors.response.use(undefined, handleUnauthorized);
