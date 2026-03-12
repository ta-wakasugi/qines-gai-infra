import { DRAG_ITEM_TYPES } from "@/consts/draggable";
import { DocumentType } from "@/models/document";
import { render, renderHook } from "@testing-library/react";
import { useSearchDocumentCard } from "./searchDocumentCard";

jest.mock("@/hooks/collection/document/useDragDropSearchCollectionDocuments", () => {
  return {
    useSearchedDocumentDrag: jest.fn(() => ({
      dragRef: { current: null },
    })),
    useSearchedDocumentDrop: jest.fn(() => ({
      dropRef: { current: null },
    })),
    useCollectionDocumentDrag: jest.fn(() => ({
      dragRef: { current: null },
    })),
    useCollectionDocumentDrop: jest.fn(() => ({
      dropRef: { current: null },
    })),
  };
});

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

describe("DocumentCard", () => {
  describe("useSearchDocumentCard", () => {
    describe("OpenDocumentIcon", () => {
      const renderUseSearchDocumentCard = (document: DocumentType) => {
        const { result } = renderHook(() =>
          useSearchDocumentCard(document, DRAG_ITEM_TYPES.SEARCHED_DOCUMENT)
        );
        const { OpenDocumentIcon } = result.current;
        const { getByTestId, queryByTestId } = render(<OpenDocumentIcon />);
        return { getByTestId, queryByTestId };
      };
      it.each([
        ["PDF", mockPdfDocument],
        ["PlainText", mockTextDocument],
      ])("ドキュメントが%sの時はPDFを開くアイコンボタンを返す", (_, doc) => {
        const { getByTestId } = renderUseSearchDocumentCard(doc);
        expect(getByTestId("openDocumentButton")).toBeInTheDocument();
      });
      it("ドキュメントがPDF or PlainTextでない時はnullを返す", () => {
        const { queryByTestId } = renderUseSearchDocumentCard(mockOtherDocument);
        expect(queryByTestId("openDocumentButton")).toBeNull();
      });
    });
    describe("CardCategoryArea", () => {
      it("ドキュメントのカテゴリーを表示するコンポーネントを返す", () => {
        const { result } = renderHook(() =>
          useSearchDocumentCard(mockPdfDocument, DRAG_ITEM_TYPES.SEARCHED_DOCUMENT)
        );
        const { CardCategoryArea } = result.current;
        const { getByTestId } = render(<CardCategoryArea />);
        expect(getByTestId("cardCategoryArea")).toBeInTheDocument();
      });
    });
  });
});
