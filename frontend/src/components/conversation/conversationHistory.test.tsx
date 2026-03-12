import { act, render, screen } from "@testing-library/react";
import { ConversationHistory } from "./conversationHistory";
import { MessageType } from "@/models/conversation";

jest.mock("@uiw/react-markdown-preview", () => ({
  __esModule: true,
  default: () => <div>Mocked MarkdownPreview</div>,
}));

jest.mock("@/actions/auth", () => ({
  getUsername: () => "test name",
}));

describe("ConversationHistory", () => {
  it("User描画確認", async () => {
    const conversation: MessageType = {
      role: "user",
      content: "test",
      metadata: {},
    };
    await act(async () => {
      render(<ConversationHistory conversation={conversation} />);
    });
    expect(screen.getByText("test")).toBeInTheDocument();
    const icon = screen.getByTestId("userMessage");
    expect(icon).toBeInTheDocument();
  });

  it("aiAgent描画確認", async () => {
    expect(null).toBeNull();
    const conversation: MessageType = {
      role: "assistant",
      content: "test",
      metadata: {},
    };
    await act(async () => {
      render(<ConversationHistory conversation={conversation} />);
    });
    const icon = screen.getByTestId("agentMessage");
    expect(icon).toBeInTheDocument();
  });
});
