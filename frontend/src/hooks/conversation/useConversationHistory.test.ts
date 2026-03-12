import { MessageType } from "@/models/conversation";
import { act, renderHook } from "@testing-library/react";
import { useConversationHistory } from "./useConversationHistory";

const message: MessageType = {
  content: "",
  metadata: {},
  role: "assistant",
};

describe("useConversationHistory", () => {
  afterEach(() => {
    // jotaiの初期化
    const { result } = renderHook(() => useConversationHistory());
    act(() => {
      result.current.setConversationHistory([]);
    });
  });
  it("初期値は空配列であること", () => {
    const { result } = renderHook(() => useConversationHistory());
    expect(result.current.conversationHistory).toEqual([]);
  });

  describe("addChatHistory", () => {
    it("単一の会話履歴を追加できること", () => {
      const { result } = renderHook(() => useConversationHistory());
      act(() => {
        result.current.addConversationHistory(message);
        result.current.addConversationHistory(message);
      });
      expect(result.current.conversationHistory).toMatchObject([message, message]);
    });

    it("複数の会話履歴を追加できること", () => {
      const { result } = renderHook(() => useConversationHistory());
      act(() => {
        result.current.addConversationHistory(message);
        result.current.addConversationHistory([message, message]);
      });
      expect(result.current.conversationHistory).toMatchObject([
        message,
        message,
        message,
      ]);
    });
  });
  describe("removeLastChatHistory", () => {
    it("最新会話履歴を削除できること", () => {
      const { result } = renderHook(() => useConversationHistory());
      act(() => {
        result.current.addConversationHistory(message);
        result.current.addConversationHistory(message);
        result.current.removeLastConversationHistory();
      });
      expect(result.current.conversationHistory).toMatchObject([message]);
    });
  });
});
