import { apiClient, mockApiClient as testApiClient } from "@/api/apiClient";
import { CollectionBaseType, CollectionDetailType } from "@/models/collection";
import {
  createCollection,
  deleteCollection,
  getCollectionDetail,
  getCollectionList,
  getCollectionShareLink,
  getConversations,
} from "./collection";

jest.mock("@/api/apiClient");
jest.mock("@/actions/auth", () => ({
  getAuthToken: () => "Bearer test-token",
}));

describe("actions collection", () => {
  it("CreateCollection: 成功時にCollectionDetailType型の値を返却すること", async () => {
    const createCollectionRequest = { name: "test name", document_ids: ["doc-id"] };
    const mockResponse: CollectionDetailType = {
      public_collection_id: "test-id",
      name: "test name",
      created_at: "2023-01-01T00:00:00Z",
      updated_at: "2023-01-01T00:00:00Z",
      documents: [
        {
          id: "doc-id",
          title: "doc title",
          path: "doc/path",
          subject: "AUTOSAR",
          genre: null,
          release: null,
          file_type: "application/pdf",
        },
      ],
    };
    (apiClient.A003 as jest.Mock).mockResolvedValue(mockResponse);
    const result = await createCollection(createCollectionRequest);
    expect(apiClient.A003).toHaveBeenCalledWith(createCollectionRequest);
    expect(result).toEqual(mockResponse);
  });
  it("CreateCollection: 失敗時にエラーがThrowされること", async () => {
    const createCollectionRequest = { name: "test name", document_ids: ["doc-id"] };
    const mockError = new Error("Test error");
    (apiClient.A003 as jest.Mock).mockRejectedValue(mockError);

    await expect(createCollection(createCollectionRequest)).rejects.toThrow(
      "Test error"
    );
  });

  it("getCollectionDetail: 成功時にCollectionDetailType型の値を返却すること", async () => {
    const publicCollectionId = "test-id";
    const mockResponse: CollectionDetailType = {
      public_collection_id: "test-id",
      name: "test name",
      created_at: "2023-01-01T00:00:00Z",
      updated_at: "2023-01-01T00:00:00Z",
      documents: [
        {
          id: "doc-id",
          title: "doc title",
          path: "doc/path",
          subject: "AUTOSAR",
          genre: null,
          release: null,
          file_type: "application/pdf",
        },
      ],
    };
    (apiClient.A005 as jest.Mock).mockResolvedValue(mockResponse);
    const result = await getCollectionDetail(publicCollectionId);
    expect(apiClient.A005).toHaveBeenCalledWith({
      params: { public_collection_id: publicCollectionId },
    });
    expect(result).toEqual(mockResponse);
  });
  it("getCollectionDetail: 失敗時にエラーがThrowされること", async () => {
    const publicCollectionId = "test-id";
    const mockError = new Error("Test error");
    (apiClient.A005 as jest.Mock).mockRejectedValue(mockError);

    await expect(getCollectionDetail(publicCollectionId)).rejects.toThrow("Test error");
  });

  it("getCollectionList: 成功時にCollectionBaseType型の値を返却すること", async () => {
    const mockResponse: CollectionBaseType = {
      name: "test name",
      created_at: "2023-01-01T00:00:00Z",
      updated_at: "2023-01-01T00:00:00Z",
      public_collection_id: "test-id",
    };
    (apiClient.A004 as jest.Mock).mockResolvedValue(mockResponse);
    const result = await getCollectionList(1);
    expect(apiClient.A004).toHaveBeenCalled();
    expect(result).toEqual(mockResponse);
  });
  it("getCollectionList: 失敗時にエラーがThrowされること", async () => {
    const mockError = new Error("Test error");
    (apiClient.A004 as jest.Mock).mockRejectedValue(mockError);

    await expect(getCollectionList(1)).rejects.toThrow("Test error");
  });

  it("getConversations: 成功時にCollectionBaseType[]型の値を返却すること", async () => {
    const mockResponse: CollectionBaseType[] = [
      {
        name: "test name",
        created_at: "2023-01-01T00:00:00Z",
        updated_at: "2023-01-01T00:00:00Z",
        public_collection_id: "test-id",
      },
    ];
    (apiClient.A008 as jest.Mock).mockResolvedValue(mockResponse);
    const result = await getConversations("test");
    expect(apiClient.A008).toHaveBeenCalled();
    expect(result).toEqual(mockResponse);
  });
  it("getConversations: 失敗時にエラーがThrowされること", async () => {
    const mockError = new Error("Test error");
    (apiClient.A008 as jest.Mock).mockRejectedValue(mockError);

    await expect(getConversations("test")).rejects.toThrow("Test error");
  });

  it("getCollectionShareLink: 成功時にstring型の値を返却すること", async () => {
    const mockResponse = {
      url: "link",
    };
    (testApiClient.A014 as jest.Mock).mockResolvedValue(mockResponse);
    const result = await getCollectionShareLink("test");
    expect(testApiClient.A014).toHaveBeenCalled();
    expect(result).toEqual(mockResponse);
  });
  it("getCollectionShareLink: 失敗時にエラーがThrowされること", async () => {
    const mockError = new Error("Test error");
    (testApiClient.A014 as jest.Mock).mockRejectedValue(mockError);

    await expect(getCollectionShareLink("test")).rejects.toThrow("Test error");
  });

  it("deleteCollection: 成功時にObject型の値を返却すること", async () => {
    const mockResponse = {};
    (testApiClient.A007 as jest.Mock).mockResolvedValue(mockResponse);
    const result = await deleteCollection("test");
    expect(testApiClient.A007).toHaveBeenCalled();
    expect(result).toEqual(mockResponse);
  });
  it("deleteCollection: 失敗時にエラーがThrowされること", async () => {
    const mockError = new Error("Test error");
    (testApiClient.A007 as jest.Mock).mockRejectedValue(mockError);

    await expect(deleteCollection("test")).rejects.toThrow("Test error");
  });
});
