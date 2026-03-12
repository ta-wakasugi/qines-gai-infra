import { act, render, renderHook, waitFor } from "@testing-library/react";
import FileUploader from "./fileUploader";
import { useCollection } from "@/hooks/collection/useCollection";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";
import { useError } from "@/hooks/useError";
import userEvent from "@testing-library/user-event";
import { useDragDropUpload } from "@/hooks/useDragDropUpload";

jest.mock("@/actions/document", () => ({
  uploadDocument: jest.fn(),
}));
jest.mock("@/actions/collection");
jest.mock("@/hooks/collection/useCollection");
jest.mock("@/hooks/useButtonDisabled");
jest.mock("@/hooks/useError");
jest.mock("@/api/apiClient");
jest.mock("@/actions/auth", () => ({
  getAuthToken: () => "Bearer test-token",
}));

describe("FileUploader", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    const mockSetCollection = jest.fn();
    const mockSetCommonButtonDisabled = jest.fn();
    const mockShowError = jest.fn();

    (useCollection as jest.Mock).mockReturnValue({
      collection: { public_collection_id: "123", name: "Test Collection" },
      setCollection: mockSetCollection,
      getDocumentIds: () => [],
    });
    (useButtonDisabled as jest.Mock).mockReturnValue({
      setCommonButtonDisabled: mockSetCommonButtonDisabled,
    });
    (useError as jest.Mock).mockReturnValue({
      showError: mockShowError,
      errorTemplate: { api: "API Error" },
    });
  });

  it("レンダリング確認", async () => {
    let result: any; // eslint-disable-line @typescript-eslint/no-explicit-any
    await act(async () => {
      const hook = renderHook(() => useDragDropUpload());
      result = hook.result;
    });
    const getInputProps = result.current.getInputProps;
    const { getByText } = render(
      <FileUploader
        getInputProps={getInputProps}
        buttonLabel="ドラッグでアップロード"
        isUploadOnly={false}
        open={() => {}}
      />
    );
    expect(getByText("ドラッグでアップロード")).toBeInTheDocument();
  });

  it("ドラッグ&ドロップ時にsubmitされること", async () => {
    let result: any; // eslint-disable-line @typescript-eslint/no-explicit-any
    await act(async () => {
      const hooks = renderHook(() => useDragDropUpload());
      result = hooks.result;
    });
    const getInputProps = result.current.getInputProps;
    const { getByTestId } = render(
      <FileUploader
        getInputProps={getInputProps}
        buttonLabel="ドラッグでアップロード"
        isUploadOnly={false}
        open={() => {}}
      />
    );
    const input = getByTestId("file");
    const file = new File(["dummy content"], "example.csv", { type: "text/csv" });

    const form = input.closest("form") as HTMLFormElement;
    const requestSubmitSpy = jest.spyOn(form, "requestSubmit");

    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(requestSubmitSpy).toHaveBeenCalled();
    });
  });

  it("閾値を超えるファイルの場合はエラーとなること", async () => {
    const mockShowError = jest.fn();
    (useError as jest.Mock).mockReturnValue({
      showError: mockShowError,
      errorTemplate: { api: "API Error" },
    });

    const { result } = renderHook(() => useDragDropUpload());
    const getInputProps = result.current.getInputProps;
    const { getByTestId } = render(
      <FileUploader
        getInputProps={getInputProps}
        buttonLabel="ドラッグでアップロード"
        isUploadOnly={false}
        open={() => {}}
      />
    );
    const input = getByTestId("file");
    const largeFile = new File(["a".repeat(6 * 1024 * 1024)], "largeFile.txt", {
      type: "text/plain",
    });
    await userEvent.upload(input, largeFile);

    await waitFor(() => {
      expect(mockShowError).toHaveBeenCalledWith(
        "5MB以下のファイルをアップロードしてください"
      );
    });
  });
});
