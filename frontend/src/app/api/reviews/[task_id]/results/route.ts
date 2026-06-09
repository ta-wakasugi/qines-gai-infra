"use server";

import { getAuthToken } from "@/actions/auth";
import { baseUrl } from "@/api/baseUrl";

export const GET = async (
  _request: Request,
  { params }: { params: { task_id: string } }
) => {
  const url = baseUrl + `/reviews/${params.task_id}/results`;

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
