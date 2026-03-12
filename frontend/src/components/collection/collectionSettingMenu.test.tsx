import { render, act, screen, waitFor } from "@testing-library/react";
import { CollectionSettingMenu } from "./collectionSettingMenu";
import userEvent from "@testing-library/user-event";

describe("CollectionSettingMenu", () => {
  const mockShareLink = jest.fn();
  const mockDelete = jest.fn();
  const mockProps = {
    deleteTitle: "コレクション削除",
    deleteMessage: "コレクションを削除しますか？",
    deleteItem: mockDelete,
    getShareLink: mockShareLink,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("レンダリング確認", async () => {
    await act(async () => {
      render(<CollectionSettingMenu {...mockProps} />);
    });
    expect(screen.queryByText("共有")).not.toBeInTheDocument();
    expect(screen.queryByText("削除")).not.toBeInTheDocument();
  });

  it("ボタンクリック時、ポップアップが表示されること", async () => {
    await act(async () => {
      render(<CollectionSettingMenu {...mockProps} />);
    });
    await act(async () => {
      await userEvent.click(screen.getByText("･･･"));
    });
    expect(screen.queryByText("共有")).toBeInTheDocument();
    expect(screen.queryByText("削除")).toBeInTheDocument();
  });

  it("共有クリック時：メニューが閉じられてクリップボードにコピーされること", async () => {
    const mockUrl = "test url";
    const mockClipboard = {
      writeText: jest.fn().mockResolvedValue(undefined),
    };
    Object.assign(navigator, { clipboard: mockClipboard });

    await act(async () => {
      render(<CollectionSettingMenu {...mockProps} />);
    });
    await act(async () => {
      await userEvent.click(screen.getByText("･･･"));
    });
    await act(async () => {
      await userEvent.click(screen.getByText("共有"));
    });
    waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockUrl);
      expect(mockShareLink).toHaveBeenCalled();
      expect(screen.queryByText("共有")).not.toBeInTheDocument();
    });
  });

  it("削除クリック時：削除確認モーダル表示確認", async () => {
    await act(async () => {
      render(<CollectionSettingMenu {...mockProps} />);
    });
    await act(async () => {
      await userEvent.click(screen.getByText("･･･"));
    });
    await act(async () => {
      await userEvent.click(screen.getByText("削除"));
    });
    expect(screen.getByText("コレクション削除")).toBeInTheDocument();
    expect(screen.getByText("コレクションを削除しますか？")).toBeInTheDocument();
  });

  it("削除確認モーダルで削除実行時に削除処理が呼ばれること", async () => {
    await act(async () => {
      render(<CollectionSettingMenu {...mockProps} />);
    });
    await act(async () => {
      await userEvent.click(screen.getByText("･･･"));
    });
    await act(async () => {
      await userEvent.click(screen.getByText("削除"));
    });
    await act(async () => {
      await userEvent.click(screen.getByTestId("deleteConfirmButton"));
    });
    expect(mockDelete).toHaveBeenCalled();
  });

  it("削除確認モーダルで削除キャンセル時に削除処理が呼ばれないこと", async () => {
    await act(async () => {
      render(<CollectionSettingMenu {...mockProps} />);
    });
    await act(async () => {
      await userEvent.click(screen.getByText("･･･"));
    });
    await act(async () => {
      await userEvent.click(screen.getByText("削除"));
    });
    await act(async () => {
      await userEvent.click(screen.getByText("キャンセル"));
    });
    expect(mockDelete).not.toHaveBeenCalled();
  });
});
