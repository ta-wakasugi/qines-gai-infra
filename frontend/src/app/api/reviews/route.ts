"use server";

import { getAuthToken } from "@/actions/auth";
import { baseUrl } from "@/api/baseUrl";

export const POST = async (request: Request) => {
  const body = await request.json();

  const url = baseUrl + "/reviews";

  const response = await fetch(url, {
    method: "POST",
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
