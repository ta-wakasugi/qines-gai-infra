import { act, render, renderHook, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SaveCollectionModal } from "./saveCollectionModal";
import { useRouter } from "next/navigation";
import { createCollection, updateCollection } from "@/actions/collection";
import { useCollection } from "@/hooks/collection/useCollection";

jest.mock("@/actions/collection");
jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));
jest.mock("@/actions/auth", () => ({
  getAuthToken: () => "Bearer test-token",
}));

const mockCreateCollection = createCollection as jest.Mock;
const mockUpdateCollection = updateCollection as jest.Mock;
const mockUseRouter = useRouter as jest.Mock;

const collectionName = "Test Collection";
const documentIds = ["1", "2"];

describe("CreateCollectionModal", () => {
  const handleCloseModal = jest.fn();
  const push = jest.fn();
  mockCreateCollection.mockResolvedValue({
    public_collection_id: "123",
    name: collectionName,
    documents: documentIds,
    created_at: "",
    updated_at: "",
  });
  mockUpdateCollection.mockResolvedValue({
    public_collection_id: "123",
    name: collectionName,
    documents: documentIds,
    created_at: "",
    updated_at: "",
  });

  beforeEach(() => {
    mockUseRouter.mockReturnValue({ push });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  const renderComponent = (isModalOpen: boolean) =>
    render(
      <SaveCollectionModal
        isModalOpen={isModalOpen}
        handleCloseModal={handleCloseModal}
        documentIds={documentIds}
      />
    );

  it("モーダルが表示されること", () => {
    renderComponent(true);
    expect(screen.getByTestId("save-collection-modal")).toBeInTheDocument();
  });

  it("モーダルが表示されないこと", () => {
    renderComponent(false);
    expect(screen.queryByTestId("save-collection-modal")).not.toBeInTheDocument();
  });

  it("クローズアイコンが押下されたら、handleCloseModal()が呼ばれる", async () => {
    renderComponent(true);
    await userEvent.click(screen.getByTestId("close-modal-icon"));
    expect(handleCloseModal).toHaveBeenCalled();
  });

  it("inputが空であれば、ボタンは非活性", () => {
    renderComponent(true);
    expect(screen.getByRole("button", { name: "保存" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "保存して新規チャット" })).toBeDisabled();
  });

  it("inputが空でなければ、ボタンは活性化", async () => {
    renderComponent(true);
    await userEvent.type(screen.getByPlaceholderText("コレクション名"), collectionName);
  });

  it("保存ボタンが押下されたら、submit処理が実行されコレクト編集画面に遷移する", async () => {
    renderComponent(true);
    await userEvent.type(screen.getByPlaceholderText("コレクション名"), collectionName);
    const button = screen.getByRole("button", { name: "保存" });

    // SubmitEventが取得できないのでmock化する
    const form = button.closest("form");
    const mockSubmitEvent = new Event("submit", { bubbles: true }) as SubmitEvent;
    Object.defineProperty(mockSubmitEvent, "submitter", {
      value: button,
      writable: true,
    });
    await act(async () => {
      form?.dispatchEvent(mockSubmitEvent);
    });
    await userEvent.click(button);
    expect(createCollection).toHaveBeenCalledWith({
      name: collectionName,
      document_ids: documentIds,
    });
    expect(handleCloseModal).toHaveBeenCalled();
    expect(push).toHaveBeenCalledWith("/collections/123");
  });

  it("保存して新規チャットボタンが押下されたら、submit処理が実行されチャット画面に遷移する", async () => {
    renderComponent(true);
    await userEvent.type(screen.getByPlaceholderText("コレクション名"), collectionName);
    const button = screen.getByRole("button", { name: "保存して新規チャット" });

    // SubmitEventが取得できないのでmock化する
    const form = button.closest("form");
    const mockSubmitEvent = new Event("submit", { bubbles: true }) as SubmitEvent;
    Object.defineProperty(mockSubmitEvent, "submitter", {
      value: button,
      writable: true,
    });
    await act(async () => {
      form?.dispatchEvent(mockSubmitEvent);
    });

    await userEvent.click(button);
    expect(updateCollection).toHaveBeenCalled();
    expect(handleCloseModal).toHaveBeenCalled();
    expect(push).toHaveBeenCalledWith("/collections/123/chat/new");
  });

  it("更新時にはupdateCollectionがコールされること", async () => {
    const { result } = renderHook(() => useCollection());
    await act(async () => {
      result.current.setCollection({
        public_collection_id: "123",
        name: collectionName,
        documents: [],
        created_at: "",
        updated_at: "",
      });
    });
    renderComponent(true);
    await userEvent.type(screen.getByPlaceholderText("コレクション名"), collectionName);
    const button = screen.getByRole("button", { name: "保存" });

    // SubmitEventが取得できないのでmock化する
    const form = button.closest("form");
    const mockSubmitEvent = new Event("submit", { bubbles: true }) as SubmitEvent;
    Object.defineProperty(mockSubmitEvent, "submitter", {
      value: button,
      writable: true,
    });
    await act(async () => {
      form?.dispatchEvent(mockSubmitEvent);
    });
    await userEvent.click(button);
    expect(mockUpdateCollection).toHaveBeenCalled();
    expect(handleCloseModal).toHaveBeenCalled();
  });
});
