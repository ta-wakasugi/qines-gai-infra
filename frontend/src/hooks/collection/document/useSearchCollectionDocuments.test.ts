import { DocumentType } from "@/models/document";
import { renderHook } from "@testing-library/react";
import { act } from "react";
import { useSearchCollectionDocuments } from "./useSearchCollectionDocuments";
import { searchDocument, deleteDocument } from "@/actions/document";

jest.mock("@/actions/document", () => ({
  searchDocument: jest.fn(),
  deleteDocument: jest.fn(),
}));

const mockedDocuments: DocumentType[] = [
  {
    id: "1",
    path: "/sample-document.pdf",
    title: "mockTitle",
    subject: "AUTOSAR",
    genre: "mockGenre",
    release: "mockRelease",
    file_type: "application/pdf",
  },
  {
    id: "2",
    path: "/sample-document.pdf",
    title: "mockTitle",
    subject: "AUTOSAR",
    genre: "mockGenre",
    release: "mockRelease",
    file_type: "application/pdf",
  },
];
describe("useSearchCollectionDocuments", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  describe("useSearchedDocuments", () => {
    it("searchedDocumentsIdsはsearchedDocumentsのidの配列", () => {
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setSearchedDocuments(mockedDocuments);
      });
      expect(result.current.searchedDocumentsIds).toEqual(["1", "2"]);
    });
    it("removeDocumentFromSearchedはsearchedDocumentsから引数のdocumentを削除", () => {
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setSearchedDocuments(mockedDocuments);
      });
      act(() => {
        result.current.removeDocumentFromSearched(mockedDocuments[0]);
      });
      expect(result.current.searchedDocuments).toEqual([mockedDocuments[1]]);
    });
  });
  describe("useCollectionDocuments", () => {
    it("collectionDocumentsIdsはcollectionDocumentsのidの配列", () => {
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setCollectionDocuments(mockedDocuments);
      });
      expect(result.current.collectionDocumentsIds).toEqual(["1", "2"]);
    });
    it("addCollectionDocumentはcollectionDocumentsに引数のdocumentを追加", () => {
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setCollectionDocuments([]);
      });
      act(() => {
        result.current.addCollectionDocument(mockedDocuments[0]);
      });
      expect(result.current.collectionDocuments).toEqual([mockedDocuments[0]]);
    });
    it("isExistInCollectionはcollectionDocumentsIdsに引数のdocumentのidが含まれている場合trueを返す", () => {
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setCollectionDocuments(mockedDocuments);
      });
      expect(result.current.isExistInCollection(mockedDocuments[0])).toBeTruthy();
      expect(
        result.current.isExistInCollection({ ...mockedDocuments[0], id: "1" })
      ).toBeTruthy();
    });
    it("isExistInCollectionはcollectionDocumentsIdsに引数のdocumentのidが含まれていない場合falseを返す", () => {
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setCollectionDocuments(mockedDocuments);
      });
      expect(
        result.current.isExistInCollection({ ...mockedDocuments[0], id: "3" })
      ).toBeFalsy();
    });
    it("removeDocumentFromCollectionはcollectionDocumentsから引数のdocumentを削除", () => {
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setCollectionDocuments(mockedDocuments);
      });
      act(() => {
        result.current.removeFromCollection(mockedDocuments[0]);
      });
      expect(result.current.collectionDocuments).toEqual([mockedDocuments[1]]);
    });
  });
  describe("useSearchDocuments", () => {
    it("searchDocumentsは検索条件がない場合、searchedDocumentsを空にする", async () => {
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setInputValue("");
        result.current.setCheckboxState({ genre: [], release: [], uploader: [] });
      });
      await act(async () => {
        await result.current.searchDocuments();
      });
      expect(result.current.searchedDocuments).toEqual([]);
    });

    it("searchDocumentsは検索条件がある場合、searchedDocumentsを設定する", async () => {
      (searchDocument as jest.Mock).mockResolvedValue({
        documents: mockedDocuments,
        total_pages: mockedDocuments.length,
      });
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setInputValue("test");
      });
      await act(async () => {
        await result.current.searchDocuments();
      });
      expect(result.current.searchedDocuments).toEqual(mockedDocuments);
    });

    it("handleChangePageはページを変更し、searchedDocumentsを更新する", async () => {
      (searchDocument as jest.Mock).mockResolvedValue({
        documents: mockedDocuments,
        total_pages: mockedDocuments.length,
      });
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setInputValue("mock");
      });
      await act(async () => {
        await result.current.handleChangePage(2);
      });
      expect(result.current.searchedDocuments).toEqual(mockedDocuments);
    });

    it("deleteUploadedDocumentはドキュメントを削除し、searchedDocumentsを更新する", async () => {
      (deleteDocument as jest.Mock).mockResolvedValue({});
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setSearchedDocuments(mockedDocuments);
      });
      await act(async () => {
        await result.current.deleteUploadedDocument(mockedDocuments[0]);
      });
      expect(result.current.searchedDocuments).toEqual([mockedDocuments[1]]);
    });

    it("deleteUploadedDocumentで最後のドキュメントを削除すると、メッセージが表示されること", async () => {
      (deleteDocument as jest.Mock).mockResolvedValue({});
      const { result } = renderHook(() => useSearchCollectionDocuments());
      act(() => {
        result.current.setSearchedDocuments([mockedDocuments[0]]);
        result.current.setCurrentPage(2);
      });
      await act(async () => {
        await result.current.deleteUploadedDocument(mockedDocuments[0]);
      });
      expect(result.current.message).toBe(
        "2ページに表示できるドキュメントはありません。"
      );
    });
  });
});
