import { DocumentType } from "@/models/document";
import { render } from "@testing-library/react";
import BaseDocumentCard from "./baseDocumentCard";

const document: DocumentType = {
  id: "1",
  path: "/sample-document.pdf",
  title: "mockTitle",
  subject: "AUTOSAR",
  genre: "mockGenre",
  release: "mockRelease",
  file_type: "application/pdf",
};

describe("BaseDocumentCard", () => {
  it("snapshot", () => {
    const { asFragment } = render(
      <BaseDocumentCard
        className=""
        document={document}
        CardCategoryArea={<>CardCategoryArea</>}
        DocumentIcon={<>DocumentIcon</>}
        OpenDocumentIcon={<>OpenDocumentIcon</>}
        AddDocumentIcon={<>AddDocumentIcon</>}
        CloseIcon={<>CloseIcon</>}
      />
    );
    expect(asFragment()).toMatchSnapshot();
  });
});
