"use server";

import { getAuthToken } from "@/actions/auth";
import { baseUrl } from "@/api/baseUrl";

export const GET = async (request: Request) => {
  const { searchParams } = new URL(request.url);
  const documentRole = searchParams.get("document_role");

  if (!documentRole) {
    return Response.json({ detail: "document_role is required" }, { status: 400 });
  }

  const url =
    baseUrl + `/reviews/documents?document_role=${encodeURIComponent(documentRole)}`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: "Bearer " + (await getAuthToken()),
    },
    cache: "no-store",
  });

  const text = await response.text();

  return new Response(text, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
    },
  });
};
