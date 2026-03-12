import { render, screen, renderHook, waitFor } from "@testing-library/react";
import { ViewerContainer } from "./viewerContainer";
import userEvent from "@testing-library/user-event";
import { usePdf } from "@/hooks/pdf/usePdf";

jest.mock("@/actions/auth", () => {
  return {
    getAuthToken: () => "Bearer token", // 変数を初期化前に設定できないため固定値で指定
  };
});

jest.mock("@/hooks/useButtonDisabled", () => ({
  useButtonDisabled: () => ({ commonButtonDisabled: false }),
}));

jest.mock("@uiw/react-markdown-preview", () => ({
  __esModule: true,
  default: () => <div>Mocked MarkdownPreview</div>,
}));

const mockPdf = jest.fn();
jest.mock("@/hooks/pdf/usePdf", () => ({
  usePdf: () => ({ base64Pdf: null, resetPdf: mockPdf }),
}));

const mockArtifact = jest.fn();
const mockSetArtifact = jest.fn();
const mockGetArtifact = jest.fn();
jest.mock("@/hooks/conversation/useArtifact", () => ({
  useArtifact: () => ({
    artifact: { id: "1", title: "Test Artifact", version: 1, content: "Test Content" },
    resetArtifact: mockArtifact,
    setArtifact: mockSetArtifact,
    getArtifactByIdAndVersion: mockGetArtifact,
    getMaxVersionById: () => 2,
  }),
}));

describe("ViewerContainer", () => {
  it("レンダリング確認", () => {
    const { getByText } = render(<ViewerContainer />);
    expect(getByText("Test Artifact")).toBeInTheDocument();
  });

  it("PDFを表示しているときにArtifactタイトルクリックでPDFを閉じること", async () => {
    const { result } = renderHook(() => usePdf());
    result.current.base64Pdf = "test";
    render(<ViewerContainer />);
    await userEvent.click(screen.getByText("Test Artifact"));
    expect(mockPdf).toHaveBeenCalled();
  });

  it("artifact閉じるボタンでartifact表示が閉じられること", async () => {
    render(<ViewerContainer />);
    await userEvent.click(screen.getByText("×"));
    expect(mockArtifact).toHaveBeenCalled();
  });

  it("ボタンの非活性確認", () => {
    jest
      .spyOn(require("@/hooks/useButtonDisabled"), "useButtonDisabled") // eslint-disable-line @typescript-eslint/no-var-requires
      .mockReturnValue({
        commonButtonDisabled: true,
      });
    render(<ViewerContainer />);
    expect(screen.getByText("×")).toBeDisabled();
  });

  it("バージョンを変更した際にartifactが変更されること", async () => {
    render(<ViewerContainer />);
    const select = screen.getByRole("combobox");
    await userEvent.selectOptions(select, "2");
    waitFor(() => {
      expect(mockGetArtifact).toHaveBeenCalled();
      expect(mockArtifact).toHaveBeenCalled();
    });
  });
});
