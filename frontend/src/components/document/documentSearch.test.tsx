import { DocumentType } from "@/models/document";
import { act, render, renderHook, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DocumentSearch, {
  DocumentSearchView,
  useDocumentSearch,
} from "./documentSearch";

jest.mock("@/actions/auth", () => ({
  getAuthToken: () => "Bearer test-token",
}));

const mockedDocument: DocumentType = {
  id: "1",
  title: "title",
  genre: "genre",
  release: "release",
  path: "path",
  subject: "AUTOSAR",
  file_type: "application/pdf",
};
const nonAutosarDocument: DocumentType = { ...mockedDocument, subject: "others" };

const mockDeleteUploadedDocument = jest.fn();

// useSearchCollectionDocumentsのdeleteUploadedDocumentのみモック
jest.mock("@/hooks/collection/document/useSearchCollectionDocuments", () => {
  const actual = jest.requireActual(
    "@/hooks/collection/document/useSearchCollectionDocuments"
  );
  return {
    ...actual,
    useSearchCollectionDocuments: () => ({
      ...actual.useSearchCollectionDocuments(),
      deleteUploadedDocument: mockDeleteUploadedDocument,
    }),
  };
});

jest.mock("@/actions/document", () => ({
  searchDocument: jest.fn(() => Promise.resolve({ documents: [mockedDocument] })),
}));

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

describe("DocumentSearch", () => {
  const PROCESSING_MESSAGE = "検索中...";
  const NOT_FOUND_MESSAGE = "ドキュメントが見つかりませんでした。";
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("初期描画が正しいこと", () => {
    render(<DocumentSearch />);
    expect(screen.getByPlaceholderText("キーワード")).toBeInTheDocument();
    expect(screen.getByTestId("filter-icon")).toBeInTheDocument();
    expect(screen.queryByText(NOT_FOUND_MESSAGE)).not.toBeInTheDocument();
    expect(screen.queryByText("searchFilter")).not.toBeInTheDocument();
    expect(screen.queryByTestId("delete-confirm-modal")).not.toBeInTheDocument();
  });

  it("キーワード入力ができること", async () => {
    render(<DocumentSearch />);
    const input = screen.getByPlaceholderText("キーワード");
    await act(async () => {
      await userEvent.type(input, "test");
    });
    expect(input).toHaveValue("test");
  });

  it("検索結果がなければ、メッセージを表示する", async () => {
    await act(async () => {
      render(
        <DocumentSearchView
          hooks={{
            inputValue: "test",
            setInputValue: jest.fn(),
            handleSubmit: jest.fn(),
            searchedDocuments: [],
            message: NOT_FOUND_MESSAGE,
            pageCount: 0,
            currentPage: 0,
            isVisibleFilter: false,
            setIsVisibleFilter: jest.fn(),
            handleChangePage: jest.fn(),
            RemoveDocument: jest.fn(),
            dropRef: { current: null },
          }}
        />
      );
    });
    expect(screen.queryByText(NOT_FOUND_MESSAGE)).toBeInTheDocument();
  });

  it("検索中メッセージを表示する", async () => {
    await act(async () => {
      render(
        <DocumentSearchView
          hooks={{
            inputValue: "test",
            setInputValue: jest.fn(),
            handleSubmit: jest.fn(),
            searchedDocuments: [],
            message: PROCESSING_MESSAGE,
            pageCount: 1,
            currentPage: 1,
            isVisibleFilter: false,
            setIsVisibleFilter: jest.fn(),
            handleChangePage: jest.fn(),
            RemoveDocument: jest.fn(),
            dropRef: { current: null },
          }}
        />
      );
    });
    expect(screen.queryByText(PROCESSING_MESSAGE)).toBeInTheDocument();
    expect(screen.queryByText(NOT_FOUND_MESSAGE)).not.toBeInTheDocument();
  });

  it("検索結果があれば、ドキュメントを表示する", async () => {
    render(
      <DocumentSearchView
        hooks={{
          inputValue: "test",
          setInputValue: jest.fn(),
          handleSubmit: jest.fn(),
          searchedDocuments: [mockedDocument],
          message: NOT_FOUND_MESSAGE,
          pageCount: 1,
          currentPage: 1,
          isVisibleFilter: false,
          setIsVisibleFilter: jest.fn(),
          handleChangePage: jest.fn(),
          RemoveDocument: jest.fn(),
          dropRef: { current: null },
        }}
      />
    );
    waitFor(() => {
      expect(screen.queryByText("title")).toBeInTheDocument();
      expect(screen.queryByText("genre")).toBeInTheDocument();
      expect(screen.queryByText("release")).toBeInTheDocument();
      expect(screen.queryByText(PROCESSING_MESSAGE)).not.toBeInTheDocument();
      expect(screen.queryByText(NOT_FOUND_MESSAGE)).not.toBeInTheDocument();
    });
  });

  it("ページネーションが動作すること", async () => {
    const handleChangePage = jest.fn();
    await act(async () => {
      render(
        <DocumentSearchView
          hooks={{
            inputValue: "test",
            setInputValue: jest.fn(),
            handleSubmit: jest.fn(),
            searchedDocuments: [mockedDocument],
            message: "",
            pageCount: 3,
            currentPage: 1,
            isVisibleFilter: false,
            setIsVisibleFilter: jest.fn(),
            handleChangePage,
            RemoveDocument: jest.fn(),
            dropRef: { current: null },
          }}
        />
      );
    });
    const page2 = screen.getByRole("button", { name: "Go to page 2" });
    await act(async () => {
      await userEvent.click(page2);
    });
    expect(handleChangePage).toHaveBeenCalledWith(2);
  });

  it("ドキュメントがAUTOSARの時は削除ボタンが表示されないこと", async () => {
    const { result } = renderHook(() => useDocumentSearch());
    const { RemoveDocument } = result.current;
    const { queryByRole } = render(<RemoveDocument document={mockedDocument} />);
    expect(queryByRole("button")).not.toBeInTheDocument();
  });
  it("ドキュメントがAUTOSARでない時は削除ボタンが表示されること", async () => {
    const { result } = renderHook(() => useDocumentSearch());
    const { RemoveDocument } = result.current;
    const { getByRole } = render(
      <RemoveDocument document={{ ...mockedDocument, subject: "others" }} />
    );
    expect(getByRole("button")).toBeInTheDocument();
  });

  it("検索フィルタが表示されること", async () => {
    const { result } = renderHook(() => useDocumentSearch());
    const { setIsVisibleFilter } = result.current;
    render(
      <DocumentSearchView
        hooks={{
          inputValue: "test",
          setInputValue: jest.fn(),
          handleSubmit: jest.fn(),
          searchedDocuments: [],
          message: "",
          pageCount: 1,
          currentPage: 1,
          isVisibleFilter: true,
          setIsVisibleFilter,
          handleChangePage: jest.fn(),
          RemoveDocument: jest.fn(),
          dropRef: { current: null },
        }}
      />
    );
    expect(screen.queryByTestId("popupMenu")).toBeInTheDocument();
  });

  it("isOpen:trueで、削除確認モーダルが表示されること", async () => {
    const { result } = renderHook(() => useDocumentSearch());
    await act(async () => {
      render(
        <DocumentSearchView
          hooks={{
            ...result.current,
            searchedDocuments: [mockedDocument],
            isOpen: true,
            targetDocumentId: nonAutosarDocument.id,
          }}
        />
      );
    });

    expect(screen.getByTestId("delete-confirm-modal")).toBeInTheDocument();
    expect(screen.queryByText("title")).toBeInTheDocument();
  });

  it("削除確認モーダルで削除ボタンをクリックすると、削除処理が呼ばれること", async () => {
    const { result } = renderHook(() => useDocumentSearch());
    await act(async () => {
      render(
        <DocumentSearchView
          hooks={{
            ...result.current,
            searchedDocuments: [nonAutosarDocument],
            isOpen: true,
            targetDocumentId: nonAutosarDocument.id,
          }}
        />
      );
    });

    const confirmButton = screen.getByRole("button", { name: "削除" });
    await act(async () => {
      await userEvent.click(confirmButton);
    });

    expect(mockDeleteUploadedDocument).toHaveBeenCalledWith(nonAutosarDocument);
  });

  it("削除確認モーダルでキャンセルボタンクリック時に削除処理が呼ばれないこと", async () => {
    const { result } = renderHook(() => useDocumentSearch());
    await act(async () => {
      render(
        <DocumentSearchView
          hooks={{
            ...result.current,
            searchedDocuments: [nonAutosarDocument],
            isOpen: true,
            targetDocumentId: nonAutosarDocument.id,
          }}
        />
      );
    });

    const cancelButton = screen.getByRole("button", { name: "キャンセル" });
    await act(async () => {
      await userEvent.click(cancelButton);
    });

    expect(mockDeleteUploadedDocument).not.toHaveBeenCalled();
  });

  test.todo("削除ボタンがクリックされた時、対象のドキュメントが非表示になること");
  test.todo("ページ内の最後のドキュメントが削除されたら、メッセージが表示されること");
});
