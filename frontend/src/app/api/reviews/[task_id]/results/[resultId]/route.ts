"use server";

import { getAuthToken } from "@/actions/auth";
import { baseUrl } from "@/api/baseUrl";

/**
 * レビュー結果への人間フィードバック保存API
 * human_status / human_comment などをバックエンドへ転送する
 */
export const PATCH = async (
  request: Request,
  {
    params,
  }: {
    params: {
      taskId?: string;
      resultId?: string;
      task_id?: string;
      result_id?: string;
    };
  }
) => {
  const body = await request.json();

  const taskId = params.taskId ?? params.task_id ?? "";
  const resultId = params.resultId ?? params.result_id ?? "";

  if (!taskId || taskId === "undefined") {
    return Response.json(
      {
        detail: "taskId is missing",
        params,
      },
      { status: 400 }
    );
  }

  if (!resultId || resultId === "undefined") {
    return Response.json(
      {
        detail: "resultId is missing",
        params,
      },
      { status: 400 }
    );
  }

  const normalizedBaseUrl = baseUrl.replace(/\/$/, "");

  /**
   * 重要:
   * 既存の documents API は /api/documents かもしれませんが、
   * backend の reviews API はログ上 /reviews で動いています。
   *
   * そのため baseUrl が http://backend:8000/api の場合は、
   * http://backend:8000 に戻してから /reviews を付けます。
   */
  const backendBaseUrl = normalizedBaseUrl.endsWith("/api")
    ? normalizedBaseUrl.slice(0, -4)
    : normalizedBaseUrl;

  const url =
    backendBaseUrl +
    `/reviews/${encodeURIComponent(taskId)}/results/${encodeURIComponent(resultId)}`;

  console.log("[review feedback PATCH] params:", params);
  console.log("[review feedback PATCH] backend url:", url);

  const response = await fetch(url, {
    method: "PATCH",
    headers: {
      Authorization: "Bearer " + (await getAuthToken()),
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
  });

  const text = await response.text();

  return new Response(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
    },
  });
};
