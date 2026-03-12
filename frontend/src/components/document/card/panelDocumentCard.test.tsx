import { DocumentType } from "@/models/document";
import { render, renderHook } from "@testing-library/react";
import { usePanelDocumentCard } from "./panelDocumentCard";

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

jest.mock("@/actions/auth", () => ({
  getAuthToken: () => "Bearer test-token",
}));

describe("DocumentCard", () => {
  describe("usePanelDocumentCard", () => {
    describe("OpenDocumentIcon", () => {
      const renderUsePanelDocumentCard = (document: DocumentType) => {
        const { result } = renderHook(() => usePanelDocumentCard(document));
        const { OpenDocumentIcon } = result.current;
        const { getByTestId, queryByTestId } = render(<OpenDocumentIcon />);
        return { getByTestId, queryByTestId };
      };
      it.each([
        ["PDF", mockPdfDocument],
        ["PlainText", mockTextDocument],
      ])("ドキュメントが%sの時はPDFを開くアイコンボタンを返す", (_, doc) => {
        const { getByTestId } = renderUsePanelDocumentCard(doc);
        expect(getByTestId("openPdfButton")).toBeInTheDocument();
      });
      it("ドキュメントがPDF or PlainTextでない時はnullを返す", () => {
        const { queryByTestId } = renderUsePanelDocumentCard(mockOtherDocument);
        expect(queryByTestId("openPdfButton")).toBeNull();
      });
    });
    describe("RemoveDocumentIcon", () => {
      it("ドキュメント削除アイコンボタンを返す", () => {
        const { result } = renderHook(() => usePanelDocumentCard(mockPdfDocument));
        const { RemoveDocumentIcon } = result.current;
        const { getByTestId } = render(<RemoveDocumentIcon />);
        expect(getByTestId("deleteDocumentButton")).toBeInTheDocument();
      });
    });
    describe("CardCategoryArea", () => {
      it("ドキュメントのカテゴリーを表示するコンポーネントを返す", () => {
        const { result } = renderHook(() => usePanelDocumentCard(mockPdfDocument));
        const { CardCategoryArea } = result.current;
        const { getByTestId } = render(<CardCategoryArea />);
        expect(getByTestId("cardCategoryArea")).toBeInTheDocument();
      });
    });
  });
});
