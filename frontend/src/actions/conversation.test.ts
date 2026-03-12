import { apiClient as testApiClient, mockApiClient } from "@/api/apiClient";
import { schemas } from "@/api/openapiClient";
import {
  deleteConversation,
  getConversationShareLink,
  postChatStart,
} from "./conversation";

jest.mock("@/api/apiClient", () => ({
  apiClient: {
    A012: jest.fn(),
  },
  mockApiClient: {
    A010: jest.fn(),
    A015: jest.fn(),
  },
}));
jest.mock("@/api/openapiClient");

describe("getConversation", () => {
  test.todo("APIが問題なくコールされること");
  test.todo("APIコールが失敗した場合はエラーをスローする");
});

describe("postChat", () => {
  test.todo("APIが問題なくコールされること");
  test.todo("APIコールが失敗した場合はエラーをスローする");
});

describe("postChatStart", () => {
  const requestBody = {
    message: "dummy message",
  };

  const mockResponse = {
    public_collection_id: "dummy_collection_id",
    name: "dummy_name",
    created_at: "2023-01-01T00:00:00Z",
    updated_at: "2023-01-01T00:00:00Z",
    documents: [],
  };

  it("APIが問題なくコールされること", async () => {
    (testApiClient.A012 as jest.Mock).mockResolvedValue(mockResponse);
    (schemas.CollectionDetail.parse as jest.Mock).mockReturnValue(mockResponse);
    const result = await postChatStart(requestBody);
    expect(testApiClient.A012).toHaveBeenCalledWith(requestBody);
    expect(result).toEqual(mockResponse);
    expect(schemas.CollectionDetail.parse).toHaveBeenCalledWith(mockResponse);
  });

  it("APIコールが失敗した場合はエラーをスローする", async () => {
    const error = new Error("API error");
    (testApiClient.A012 as jest.Mock).mockRejectedValue(error);

    await expect(postChatStart(requestBody)).rejects.toThrow(error);
  });
});

describe("getConversationShareLink", () => {
  const mockResponse = {
    url: "dummy_url",
  };

  it("APIが問題なくコールされること", async () => {
    (mockApiClient.A015 as jest.Mock).mockResolvedValue(mockResponse);
    const result = await getConversationShareLink("test");
    expect(mockApiClient.A015).toHaveBeenCalled();
    expect(result).toEqual(mockResponse);
  });

  it("APIコールが失敗した場合はエラーをスローする", async () => {
    const error = new Error("API error");
    (mockApiClient.A015 as jest.Mock).mockRejectedValue(error);

    await expect(getConversationShareLink("test")).rejects.toThrow(error);
  });
});

describe("deleteConversation", () => {
  const mockResponse = "success";

  it("APIが問題なくコールされること", async () => {
    (mockApiClient.A010 as jest.Mock).mockResolvedValue(mockResponse);
    const result = await deleteConversation("test");
    expect(mockApiClient.A010).toHaveBeenCalled();
    expect(result).toEqual(mockResponse);
  });

  it("APIコールが失敗した場合はエラーをスローする", async () => {
    const error = new Error("API error");
    (mockApiClient.A010 as jest.Mock).mockRejectedValue(error);

    await expect(deleteConversation("test")).rejects.toThrow(error);
  });
});
