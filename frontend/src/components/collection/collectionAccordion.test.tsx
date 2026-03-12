import { render, screen, waitFor } from "@testing-library/react";
import CollectionAccordion from "./collectionAccordion";
import { getConversations } from "@/actions/collection";
import userEvent from "@testing-library/user-event";

jest.mock("@/api/apiClient");
jest.mock("@/actions/collection");
jest.mock("@/actions/auth", () => ({
  getAuthToken: () => "Bearer test-token",
}));

describe("CollectionAccordion", () => {
  const mockCollection = {
    public_collection_id: "test-id",
    name: "Test Collection",
    created_at: "2021-01-01T00:00:00Z",
    updated_at: "2021-01-01T00:00:00Z",
  };
  const mockConversations = [
    {
      public_conversation_id: "conv-1",
      title: "Conversation 1",
    },
    {
      public_conversation_id: "conv-2",
      title: "Conversation 2",
    },
  ];

  beforeEach(() => {
    (getConversations as jest.Mock).mockReset();
  });

  it("レンダリング確認", () => {
    render(
      <CollectionAccordion
        collection={mockCollection}
        handleDeleteCollection={() => {}}
      />
    );
    expect(screen.getByText("Test Collection")).toBeInTheDocument();
  });

  it("アコーディオンを開くボタンでコンテンツが表示されること", async () => {
    (getConversations as jest.Mock).mockResolvedValue(mockConversations);
    render(
      <CollectionAccordion
        collection={mockCollection}
        handleDeleteCollection={() => {}}
      />
    );
    const accordionButton = screen.getByTestId("collectionAccordionButton");
    await userEvent.click(accordionButton);
    waitFor(() => {
      expect(screen.findByText("Conversation 1")).toBeInTheDocument();
      expect(screen.getByText("Conversation 2")).toBeInTheDocument();
    });
  });

  it("アコーディオンを開いた際にコンテンツがなければ存在しない表記となること", async () => {
    (getConversations as jest.Mock).mockResolvedValue([]);
    render(
      <CollectionAccordion
        collection={mockCollection}
        handleDeleteCollection={() => {}}
      />
    );
    const accordionButton = screen.getByTestId("collectionAccordionButton");
    await userEvent.click(accordionButton);
    waitFor(() => {
      expect(screen.getByText("会話履歴がありません")).toBeInTheDocument();
    });
  });
});
