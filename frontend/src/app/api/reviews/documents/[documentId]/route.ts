"use server";

import { getAuthToken } from "@/actions/auth";
import { baseUrl } from "@/api/baseUrl";

export const DELETE = async (
  _request: Request,
  { params }: { params: { documentId: string } }
) => {
  const { documentId } = params;

  const url = baseUrl + `/reviews/documents/${encodeURIComponent(documentId)}`;

  const response = await fetch(url, {
    method: "DELETE",
    headers: {
      Authorization: "Bearer " + (await getAuthToken()),
    },
  });

  if (response.status === 204) {
    return new Response(null, { status: 204 });
  }

  const text = await response.text().catch(() => "");

  return new Response(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
    },
  });
};
