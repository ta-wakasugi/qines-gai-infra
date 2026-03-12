import { render, screen, waitFor } from "@testing-library/react";
import { useError } from "@/hooks/useError";
import { ErrorAlert } from "./errorAlert";
import userEvent from "@testing-library/user-event";

jest.mock("@/hooks/useError");

describe("ErrorAlert", () => {
  it("エラーメッセージ設定なし：アラート表示なし", () => {
    (useError as jest.Mock).mockReturnValue({
      errorMessage: "",
      showError: jest.fn(),
    });
    const { container } = render(<ErrorAlert />);
    expect(container.firstChild).toBeNull();
  });

  it("エラーメッセージ設定あり：アラート表示あり", () => {
    (useError as jest.Mock).mockReturnValue({
      errorMessage: "エラー内容",
      showError: jest.fn(),
    });
    render(<ErrorAlert />);
    expect(screen.getByText("エラー")).toBeInTheDocument();
    expect(screen.getByText("エラー内容")).toBeInTheDocument();
  });

  it("閉じるボタンでアラートが閉じられること", async () => {
    (useError as jest.Mock).mockReturnValue({
      errorMessage: "エラー",
      showError: jest.fn(),
      hiddenError: jest.fn(),
    });
    const { container } = render(<ErrorAlert />);
    await userEvent.click(screen.getByText("×"));
    waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });
});
