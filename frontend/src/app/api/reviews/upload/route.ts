"use server";

import { getAuthToken } from "@/actions/auth";
import { baseUrl } from "@/api/baseUrl";

export const POST = async (request: Request) => {
  const formData = await request.formData();

  const url = baseUrl + "/api/documents/upload-debug";

  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: "Bearer " + (await getAuthToken()),
    },
    body: formData,
  });

  const text = await response.text();

  return new Response(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
    },
  });
};
