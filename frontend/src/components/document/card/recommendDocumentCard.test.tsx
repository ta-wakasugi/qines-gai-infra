import { DocumentType } from "@/models/document";
import { render, renderHook, waitFor } from "@testing-library/react";
import { useRecommendDocumentCard } from "./recommendDocumentCard";
import userEvent from "@testing-library/user-event";
import { updateCollection } from "@/actions/collection";

const mockDeleteRecommendDocument = jest.fn();
jest.mock("@/hooks/conversation/useRecommendDocuments", () => ({
  useRecommendDocuments: () => ({
    deleteRecommendDocument: mockDeleteRecommendDocument,
  }),
}));

const mockSetCollection = jest.fn();
jest.mock("@/hooks/collection/useCollection", () => ({
  useCollection: () => ({
    setCollection: mockSetCollection,
    collection: {
      public_collection_id: "1",
      name: "mockName",
      documents: [],
    },
  }),
}));

jest.mock("@/api/apiClient");
jest.mock("@/actions/collection", () => ({
  updateCollection: jest.fn(),
}));

const mockPdfDocument: DocumentType = {
  id: "1",
  path: "/sample-document.pdf",
  title: "mockTitle",
  subject: "AUTOSAR",
  genre: "mockGenre",
  release: "mockRelease",
  file_type: "application/pdf",
};
const mockTextDocument: DocumentType = {
  id: "2",
  path: "/sample-document.txt",
  title: "mockTitle",
  subject: "others",
  genre: "mockGenre",
  release: "mockRelease",
  file_type: "text/plain",
};
const mockOtherDocument: DocumentType = {
  id: "2",
  path: "/sample-document.json",
  title: "mockTitle",
  subject: "others",
  genre: "mockGenre",
  release: "mockRelease",
  file_type: "application/json",
};

describe("RecommendDocumentCard", () => {
  describe("useRecommendDocumentCard", () => {
    describe("OpenDocumentIcon", () => {
      const renderUseRecommendDocumentCard = (document: DocumentType) => {
        const { result } = renderHook(() => useRecommendDocumentCard(document));
        const { OpenDocumentIcon } = result.current;
        const { getByTestId, queryByTestId } = render(<OpenDocumentIcon />);
        return { getByTestId, queryByTestId };
      };
      it.each([
        ["PDF", mockPdfDocument],
        ["PlainText", mockTextDocument],
      ])("ドキュメントが%sの時はPDFを開くアイコンボタンを返す", (_, doc) => {
        const { getByTestId } = renderUseRecommendDocumentCard(doc);
        expect(getByTestId("openPdfButton")).toBeInTheDocument();
      });
      it("ドキュメントがPDF or PlainTextでない時はnullを返す", () => {
        const { queryByTestId } = renderUseRecommendDocumentCard(mockOtherDocument);
        expect(queryByTestId("openPdfButton")).toBeNull();
      });
    });
    describe("RemoveDocumentIcon", () => {
      it("ドキュメント削除アイコンボタンを返す", () => {
        const { result } = renderHook(() => useRecommendDocumentCard(mockPdfDocument));
        const { RemoveDocumentIcon } = result.current;
        const { getByTestId } = render(<RemoveDocumentIcon />);
        expect(getByTestId("deleteRecommendButton")).toBeInTheDocument();
      });
      it("削除ボタン押下時リコメンド一覧から削除する処理が実行されること", async () => {
        const { result } = renderHook(() => useRecommendDocumentCard(mockPdfDocument));
        const { RemoveDocumentIcon } = result.current;
        const { getByTestId } = render(<RemoveDocumentIcon />);
        await userEvent.click(getByTestId("deleteRecommendButton"));
        expect(mockDeleteRecommendDocument).toHaveBeenCalledWith(mockPdfDocument.id);
      });
    });
    describe("CardCategoryArea", () => {
      it("ドキュメントのカテゴリーを表示するコンポーネントを返す", () => {
        const { result } = renderHook(() => useRecommendDocumentCard(mockPdfDocument));
        const { CardCategoryArea } = result.current;
        const { getByTestId } = render(<CardCategoryArea />);
        expect(getByTestId("cardCategoryArea")).toBeInTheDocument();
      });
    });
  });
  describe("AddDocumentButton", () => {
    it("追加ボタンを返す", () => {
      const { result } = renderHook(() => useRecommendDocumentCard(mockPdfDocument));
      const { AddDocumentButton } = result.current;
      const { getByTestId } = render(<AddDocumentButton />);
      expect(getByTestId("addDocumentForm")).toBeInTheDocument();
    });
    it("追加ボタンを押した際にリコメンドの一覧から削除されてコレクションの更新処理が行われること", async () => {
      const { result } = renderHook(() => useRecommendDocumentCard(mockPdfDocument));
      const { AddDocumentButton } = result.current;
      const { getByTestId } = render(<AddDocumentButton />);
      const button = getByTestId("addDocumentButton");
      await userEvent.click(button);
      waitFor(() => {
        expect(updateCollection).toHaveBeenCalled();
        expect(mockDeleteRecommendDocument).toHaveBeenCalledWith(mockPdfDocument.id);
        expect(mockSetCollection).toHaveBeenCalled();
        expect(button).toBeEnabled();
      });
    });
  });
});
