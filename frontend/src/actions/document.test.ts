import { apiClient } from "@/api/apiClient";
import { SearchDocumentQueryType, SearchedDocumentsType } from "@/models/document";
import { deleteDocument, searchDocument } from "./document";

jest.mock("@/api/apiClient");
jest.mock("@/actions/auth", () => {
  return {
    getAuthToken: () => "Bearer token", // 変数を初期化前に設定できないため固定値で指定
  };
});

describe("searchDocument", () => {
  const mockResponse: SearchedDocumentsType = {
    total_pages: 1,
    documents: [
      {
        id: "1",
        title: "title",
        path: "path",
        subject: "AUTOSAR",
        genre: "genre",
        release: "release",
        file_type: "application/pdf",
      },
    ],
  };

  it("各種クエリを指定して、APIをコールできること", async () => {
    const query: SearchDocumentQueryType = {
      q: "test",
      genre: "fiction",
      release: "2023",
      page: 2,
      hits_per_page: 10,
      uploader: ["user"],
    };

    (apiClient.A002 as jest.Mock).mockResolvedValue(mockResponse);
    const response = await searchDocument(query);

    expect(apiClient.A002).toHaveBeenCalledWith({
      queries: query,
    });
    expect(response).toEqual(mockResponse);
  });

  it("各種クエリを指定せずに、APIをコールできること", async () => {
    const query: SearchDocumentQueryType = {
      q: null,
      genre: null,
      release: null,
      page: undefined,
      hits_per_page: undefined,
      uploader: null,
    };

    (apiClient.A002 as jest.Mock).mockResolvedValue(mockResponse);
    const response = await searchDocument(query);

    expect(apiClient.A002).toHaveBeenCalledWith({
      queries: query,
    });
    expect(response).toEqual(mockResponse);
  });

  it("APIコールが失敗した場合はエラーをスローする", async () => {
    const query: SearchDocumentQueryType = {
      q: "test",
      genre: "fiction",
      release: "2023",
      page: 2,
      hits_per_page: 10,
      uploader: ["user"],
    };
    const error = new Error("API error");
    (apiClient.A002 as jest.Mock).mockRejectedValue(error);

    await expect(searchDocument(query)).rejects.toThrow(error);
  });
});

describe("deleteDocument", () => {
  it("IDを指定してAPIをコールできること", async () => {
    const documentId = "1";

    (apiClient.A017 as jest.Mock).mockResolvedValue({});
    await deleteDocument(documentId);

    expect(apiClient.A017).toHaveBeenCalledWith(undefined, {
      params: { document_id: documentId },
    });
  });

  it("APIコールが失敗した場合はエラーをスローする", async () => {
    const documentId = "1";
    const error = new Error("API error");
    (apiClient.A017 as jest.Mock).mockRejectedValue(error);

    await expect(deleteDocument(documentId)).rejects.toThrow(error);
  });
});
