import { render, screen } from "@testing-library/react";
import { ChatStartInput, ChatStartInputView } from "./chatStartInput";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
}));
jest.mock("@/actions/auth", () => ({
  getAuthToken: () => "Bearer test-token",
}));

describe("ChatStartInput", () => {
  it("タイトル、プレースホルダーが描画されること", () => {
    render(<ChatStartInput />);
    const title = screen.getByText("まずは聞いてみる");
    const placeholder = screen.getByPlaceholderText("タスクの内容を入力してください");
    expect(title).toBeInTheDocument();
    expect(placeholder).toBeInTheDocument();
  });

  it("ヘルプアイコンが描画されること", () => {
    render(<ChatStartInput />);
    const helpIcon = screen.getByTestId("helpIcon");
    expect(helpIcon).toBeInTheDocument();
  });

  it("sendIconが描画されること", () => {
    render(<ChatStartInput />);
    const sendIcon = screen.getByTestId("sendIcon");
    expect(sendIcon).toBeInTheDocument();
  });

  // form actionでのテスト挙動が想定通りにならないため、一旦コメントアウト
  test.todo(
    "ボタン押下でrouter.push('/collections/[public_collection_id]/chat/new')が呼ばれること"
  );
  // const dummyCollectionId = "dummy_collection_id";
  // const response = {
  //   public_collection_id: dummyCollectionId,
  //   name: "dummy_name",
  //   created_at: "2023-01-01T00:00:00Z",
  //   updated_at: "2023-01-01T00:00:00Z",
  //   documents: [],
  // } as CollectionDetailType;

  // const mockRouter = { push: jest.fn() };
  // (useRouter as jest.Mock).mockReturnValue(mockRouter);
  // // postChatStartをモック
  // jest.spyOn(mockApiClient, "A012").mockResolvedValue(response);
  // render(<ChatStartInput />);
  // const input = screen.getByRole("textbox");
  // const button = screen.getByRole("button");
  // await userEvent.type(input, "dummy message");
  // await userEvent.click(button);
  // waitFor(() => {
  //   expect(mockRouter).toHaveBeenCalledWith(
  //     `/collections/${dummyCollectionId}/chat/new`
  //   );
  // });

  it.each([
    ["", false, true],
    ["dummy message", false, false],
    ["", true, true],
    ["dummy message", true, true],
  ])(
    "入力値が%s、commonButtonDisabledが%sの場合、ボタンのdisableが%sであること",
    async (inputMessage, commonButtonDisabled, expected) => {
      const hooks = {
        commonButtonDisabled,
        inputMessage,
        setInputMessage: jest.fn(),
        handleSubmit: jest.fn(),
      };

      render(<ChatStartInputView hooks={hooks} />);
      const button = screen.getByRole("button");
      if (expected) {
        expect(button).toBeDisabled();
      } else {
        expect(button).toBeEnabled();
      }
    }
  );
});
