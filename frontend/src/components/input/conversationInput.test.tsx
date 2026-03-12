import { ConversationInput } from "./conversationInput";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

jest.mock("@/hooks/useButtonDisabled", () => ({
  useButtonDisabled: () => ({
    commonButtonDisabled: false,
    setCommonButtonDisabled: jest.fn(),
  }),
}));

jest.mock("@/hooks/useError", () => ({
  useError: () => ({
    showError: jest.fn(),
    errorTemplate: { api: "API Error" },
  }),
}));

jest.mock("@/hooks/conversation/useConversationHistory", () => ({
  useConversationHistory: () => ({
    addConversationHistory: jest.fn(),
    removeLastConversationHistory: jest.fn(),
  }),
}));

jest.mock("@/hooks/conversation/useStreamingMessage", () => ({
  useStreamingMessage: () => ({
    setStreamingMessage: jest.fn(),
  }),
}));

jest.mock("@/actions/postConversation", () => ({
  postConversation: jest.fn(),
}));

describe("ConversationInput", () => {
  const props = { collectionId: "test_collection" };

  it("入力領域のレンダリング確認", () => {
    render(<ConversationInput {...props} />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByRole("button")).toBeInTheDocument();
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("入力値が空でない場合に送信ボタンが活性化すること", async () => {
    render(<ConversationInput {...props} />);
    const input = screen.getByRole("textbox");
    const user = userEvent.setup();
    await user.type(input, "test message");
    expect(screen.getByRole("button")).not.toBeDisabled();
  });

  test.todo("送信ボタンをクリックした際の挙動確認");
});
