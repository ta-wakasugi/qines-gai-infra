import { DocumentType } from "@/models/document";
import { render } from "@testing-library/react";
import { CardCategory, DocumentIcon, isPdf } from "./document";

const mockGenre = "mockGenre";
const mockRelease = "mockRelease";
const mockDocument: DocumentType = {
  id: "1",
  path: "/sample-document.pdf",
  title: "mockTitle",
  subject: "AUTOSAR",
  genre: mockGenre,
  release: mockRelease,
  file_type: "application/pdf",
};
jest.mock("@/components/icons/pdfIcon", () => ({ PdfIcon: () => <>PdfIcon</> }));
jest.mock("@/components/icons/fileIcon", () => ({
  FileIcon: () => <>FileIcon</>,
}));

describe("util/document", () => {
  describe("isPdf", () => {
    it("file_typeがapplication/pdfの場合、trueを返す", () => {
      const actual = isPdf({ ...mockDocument, file_type: "application/pdf" });
      expect(actual).toBeTruthy();
    });
    it("file_typeがapplication/pdf以外の場合、falseを返す", () => {
      const actual = isPdf({ ...mockDocument, file_type: "text/plain" });
      expect(actual).toBeFalsy();
    });
  });
  describe("DocumentIcon", () => {
    it("PDFの場合、PdfIconを返す", () => {
      const { getByText } = render(
        <DocumentIcon document={{ ...mockDocument, file_type: "application/pdf" }} />
      );
      expect(getByText("PdfIcon")).toBeInTheDocument();
    });
    it("PDF以外の場合、FileIconを返す", () => {
      const { getByText } = render(
        <DocumentIcon document={{ ...mockDocument, file_type: "text/plain" }} />
      );
      expect(getByText("FileIcon")).toBeInTheDocument();
    });
  });

  describe("CardCategory", () => {
    it("subjectがAUTOSARの場合、ジャンルとリリースを表示する", () => {
      const { getByText } = render(<CardCategory document={mockDocument} />);
      expect(getByText(mockGenre)).toBeInTheDocument();
      expect(getByText(mockRelease)).toBeInTheDocument();
    });
    it("subjectがAUTOSAR以外の場合、nullを返す", () => {
      const { container } = render(
        <CardCategory document={{ ...mockDocument, subject: "others" }} />
      );
      expect(container.firstChild).toBeNull();
    });
  });
});
