"use server";

import { getAuthToken } from "@/actions/auth";
import { baseUrl } from "@/api/baseUrl";

/**
 * チャット完了APIのエンドポイント
 * バックエンドAPIにリクエストを転送し、ストリーミングレスポンスを返す
 * @param request - POSTリクエストオブジェクト
 * @returns ストリーミングレスポンス
 */
export const POST = async (request: Request) => {
  const body = await request.json();
  const url = baseUrl + "/api/ai/chat/completions";
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + (await getAuthToken()),
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!response.body) {
    throw new Error("backend api error");
  }
  // ストリーミング形式のレスポンスを返す
  return new Response(response.body, {
    headers: {
      "Content-Type": "application/json",
      "Transfer-Encoding": "chunked",
    },
  });
};
