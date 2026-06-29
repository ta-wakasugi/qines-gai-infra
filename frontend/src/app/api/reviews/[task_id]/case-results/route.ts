"use server";

import { getAuthToken } from "@/actions/auth";
import { baseUrl } from "@/api/baseUrl";

function normalizeId(value?: string | null): string {
  if (!value) return "";
  if (value === "undefined") return "";
  if (value === "null") return "";
  return value;
}

export const GET = async (
  request: Request,
  context: {
    params:
      | { taskId?: string; task_id?: string }
      | Promise<{ taskId?: string; task_id?: string }>;
  }
) => {
  const params = await context.params;

  const taskIdFromParams = normalizeId(params.taskId ?? params.task_id);

  const pathname = new URL(request.url).pathname;
  const match = pathname.match(/\/api\/reviews\/([^/]+)\/case-results$/);
  const taskIdFromPath = normalizeId(match?.[1]);

  const taskId = taskIdFromParams || taskIdFromPath;

  console.log("case-results route params:", params);
  console.log("case-results route pathname:", pathname);
  console.log("case-results route taskId:", taskId);

  if (!taskId) {
    return new Response(JSON.stringify({ detail: "taskId is required" }), {
      status: 400,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  const url = baseUrl + `/reviews/${encodeURIComponent(taskId)}/case-results`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: "Bearer " + (await getAuthToken()),
    },
  });

  const text = await response.text();

  return new Response(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
    },
  });
};
