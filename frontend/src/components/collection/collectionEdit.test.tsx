import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useModal } from "@/hooks/useModal";
import { fireEvent, render, screen } from "@testing-library/react";
import { useRouter } from "next/navigation";
import CollectionEdit from "./collectionEdit";

jest.mock("@/actions/auth", () => ({
  getAuthToken: () => "Bearer test-token",
}));
jest.mock("@/hooks/useModal");
jest.mock("@/hooks/useButtonDisabled");
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
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

describe("CollectionEdit", () => {
  const mockUseModal = useModal as jest.Mock;
  const mockUseButtonDisabled = useButtonDisabled as jest.Mock;
  const mockUseRouter = useRouter as jest.Mock;
  const mockUploadInputProps = jest.fn();

  beforeEach(() => {
    mockUseModal.mockReturnValue({
      isOpen: false,
      showModal: jest.fn(),
      hideModal: jest.fn(),
    });

    mockUseButtonDisabled.mockReturnValue({
      commonButtonDisabled: false,
      setCommonButtonDisabled: jest.fn(),
      buttonColor: "dummy",
    });

    mockUseRouter.mockReturnValue({ push: jest.fn() });
  });

  it("初期描画", () => {
    render(
      <CollectionEdit
        collectionName="Test Collection"
        uploadInputProps={mockUploadInputProps}
        uploadDialogOpen={() => {}}
      />
    );
    const listLink = screen.getByRole("link", { name: "コレクション一覧" });
    expect(listLink).toHaveAttribute("href", "/collections");
    expect(screen.getByText("Test Collection")).toBeInTheDocument();
    expect(
      screen.getByText("ファイルをドラッグ&ドロップしてください。")
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "保存" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "保存" })).not.toBeDisabled();
  });

  it("保存ボタンが押下されたら、showModal()が実行される", () => {
    const { showModal } = useModal();
    render(
      <CollectionEdit
        collectionName="Test Collection"
        uploadInputProps={mockUploadInputProps}
        uploadDialogOpen={() => {}}
      />
    );
    const saveButton = screen.getByText("保存");
    fireEvent.click(saveButton);
    expect(showModal).toHaveBeenCalled();
  });

  it("commonButtonDisabled=trueならボタンは非活性", () => {
    mockUseButtonDisabled.mockReturnValue({
      commonButtonDisabled: true,
      setCommonButtonDisabled: jest.fn(),
      buttonColor: "dummy",
    });
    render(
      <CollectionEdit
        collectionName="Test Collection"
        uploadInputProps={mockUploadInputProps}
        uploadDialogOpen={() => {}}
      />
    );
    expect(screen.getByRole("button", { name: "保存" })).toBeDisabled();
  });
});
