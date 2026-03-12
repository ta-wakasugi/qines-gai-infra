import { render, screen } from "@testing-library/react";
import { DownloadMenu } from "./downloadMenu";
import { useError } from "@/hooks/useError";
import { useButtonDisabled } from "@/hooks/useButtonDisabled";

// Mock the hooks
jest.mock("@/hooks/useError");
jest.mock("@/hooks/useButtonDisabled");
jest.mock("@/actions/auth", () => {
  return {
    getAuthToken: () => "Bearer token", // 変数を初期化前に設定できないため固定値で指定
  };
});

describe("DownloadMenu", () => {
  const mockProps = {
    isVisible: true,
    onClose: jest.fn(),
    artifact: {
      id: "1",
      version: 1,
      title: "test",
      content: "test",
    },
  };

  beforeEach(() => {
    // Mock hook implementations
    (useError as jest.Mock).mockReturnValue({
      showError: jest.fn(),
      errorTemplate: { api: "API Error" },
    });
    (useButtonDisabled as jest.Mock).mockReturnValue({
      setCommonButtonDisabled: jest.fn(),
      commonButtonDisabled: false,
    });
  });

  it("レンダリング確認", () => {
    render(<DownloadMenu {...mockProps} />);
    expect(screen.getByText("Markdown")).toBeInTheDocument();
    expect(screen.getByText("PowerPoint")).toBeInTheDocument();
    expect(screen.getByText("PDF")).toBeInTheDocument();
  });
  it("visibleがfalseの際はレンダリングされないこと", () => {
    render(<DownloadMenu {...mockProps} isVisible={false} />);
    expect(screen.queryByText("Markdown")).not.toBeInTheDocument();
  });
  it("commonButtonDisabledがtrueの場合、ボタンが非活性であること", () => {
    (useButtonDisabled as jest.Mock).mockReturnValue({
      setCommonButtonDisabled: jest.fn(),
      commonButtonDisabled: true,
    });
    render(<DownloadMenu {...mockProps} />);
    expect(screen.getByText("Markdown")).toBeDisabled();
    expect(screen.getByText("PowerPoint")).toBeDisabled();
    expect(screen.getByText("PDF")).toBeDisabled();
  });
});
