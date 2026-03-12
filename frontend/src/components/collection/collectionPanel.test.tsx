import { CollectionDetailType } from "@/models/collection";
import { act, render, renderHook, screen } from "@testing-library/react";
import CollectionPanel from "./collectionPanel";
import userEvent from "@testing-library/user-event";
import { useCollection } from "@/hooks/collection/useCollection";
import { getConversations } from "@/actions/collection";

const mockCollection: CollectionDetailType = {
  public_collection_id: "123",
  name: "Test Collection",
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-01-02T00:00:00Z",
  documents: [
    {
      id: "1",
      title: "Document 1",
      content: "Content 1",
      path: "path1",
      subject: "AUTOSAR",
      file_type: "application/pdf",
    },
    {
      id: "2",
      title: "Document 2",
      content: "Content 2",
      path: "path2",
      subject: "others",
      file_type: "application/pdf",
    },
  ],
};

jest.mock("@/actions/auth", () => ({
  getAuthToken: () => "Bearer test-token",
}));
jest.mock("@/actions/collection", () => ({
  getConversations: jest.fn(),
}));

describe("CollectionPanel", () => {
  it("ドキュメントありの場合、それぞれのカードが描画されること", async () => {
    const { result } = renderHook(() => useCollection());
    act(() => {
      result.current.setCollection(mockCollection);
    });
    await act(async () => {
      render(<CollectionPanel collectionId="123" panelWidth="300px" />);
    });
    expect(screen.getByText("Document 1")).toBeInTheDocument();
    expect(screen.getByText("Document 2")).toBeInTheDocument();
  });

  it("ドキュメントなしの場合、カードは描画されないこと", async () => {
    const emptyCollection = { ...mockCollection, documents: [] };
    const { result } = renderHook(() => useCollection());
    act(() => {
      result.current.setCollection(emptyCollection);
    });
    await act(async () => {
      render(<CollectionPanel collectionId="123" panelWidth="300px" />);
    });
    expect(screen.getByText("ドキュメントがありません")).toBeInTheDocument();
  });

  it("パネルタイプの切り替えが正しく機能すること", async () => {
    const { getByText, queryByText, queryByTestId } = render(
      <CollectionPanel collectionId="123" panelWidth="300px" />
    );
    // デフォルトでドキュメントタブが選択されていることを確認
    expect(queryByText("ドキュメント")).toHaveClass("bg-light-gray");
    expect(queryByText("ドラッグでアップロード")).toBeInTheDocument();
    expect(queryByTestId("chat-list")).not.toBeInTheDocument();
    // 会話履歴クリック後、会話履歴タブが選択されることを確認
    await userEvent.click(getByText("会話履歴"));
    expect(queryByText("ドキュメント")).not.toHaveClass("bg-light-gray");
    expect(queryByText("ドラッグでアップロード")).not.toBeInTheDocument();
    expect(queryByText("会話履歴")).toHaveClass("bg-light-gray");
    expect(queryByTestId("chatList")).toBeInTheDocument();
  });

  it("会話履歴なし", async () => {
    (getConversations as jest.Mock).mockResolvedValue([]);
    const { getByText, queryByText } = render(
      <CollectionPanel collectionId="123" panelWidth="300px" />
    );
    await userEvent.click(getByText("会話履歴"));
    expect(queryByText("会話履歴がありません")).toBeInTheDocument();
  });

  it("会話履歴あり", async () => {
    (getConversations as jest.Mock).mockResolvedValue([
      { public_conversation_id: "test", title: "testTitle" },
    ]);
    const { getByText, queryByText } = render(
      <CollectionPanel collectionId="123" panelWidth="300px" />
    );
    await userEvent.click(getByText("会話履歴"));
    expect(queryByText("testTitle")).toBeInTheDocument();
  });
});
