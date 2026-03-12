import { apiClient as testApiClient } from "@/api/apiClient";
import { downloadArtifact } from "./artifact";

jest.mock("@/api/apiClient");
jest.mock("@/actions/auth", () => ({
  getAuthToken: () => "Bearer test-token",
}));

describe("actions artifact", () => {
  it("downloadArtifact: 正常成功", async () => {
    const testRequest = {
      artifact_id: "test-id",
      version: 1,
      format: "pptx",
    };
    const mockResponse = {
      content: "test content",
      format: "pptx",
    };
    (testApiClient.A020 as jest.Mock).mockResolvedValue(mockResponse);
    const result = await downloadArtifact(testRequest);
    expect(testApiClient.A020).toHaveBeenCalled();
    expect(result).toEqual(mockResponse);
  });
  it("downloadArtifact: 失敗時にエラーがThrowされること", async () => {
    const testRequest = {
      artifact_id: "test-id",
      version: 1,
      format: "pptx",
    };
    const mockError = new Error("Test error");
    (testApiClient.A020 as jest.Mock).mockRejectedValue(mockError);

    await expect(downloadArtifact(testRequest)).rejects.toThrow("Test error");
  });
});
