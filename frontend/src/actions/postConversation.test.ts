import { postConversation } from "./postConversation";
import { ChatRequestType } from "@/models/conversation";

describe("postConversation", () => {
  const mockUpdateStreamingMessage = jest.fn();

  beforeEach(() => {
    global.fetch = jest.fn();
  });

  it("APIレスポンスが空の場合、エラーがthrowされること", async () => {
    const mockParams: ChatRequestType = {
      message: "CANドライバの初期化手順はどのように定義されていますか？",
      public_collection_id: "V1StGXR8_Z5",
      public_conversation_id: "Zf2k6A6R5h2",
    };

    const mockResponse = {
      body: null,
    };

    (global.fetch as jest.Mock).mockResolvedValue(mockResponse);
    await expect(
      postConversation(mockParams, mockUpdateStreamingMessage)
    ).rejects.toThrow("route api error");
  });

  test.todo("APIレスポンスが正常の場合、ストリーミングメッセージが更新されること");
});
