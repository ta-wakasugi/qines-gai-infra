import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import IntegerInput from "./integerInput";
describe("IntegerInput", () => {
  describe("境界値テスト", () => {
    it.each([
      [-1, 15, -2, "-"],
      [-1, 15, -1, "-1"],
      [-1, 15, 15, "15"],
      [-1, 15, 16, "1"],
    ])(
      `min=%i, max=%iのとき、%iを入力すると結果は%sになる`,
      async (min, max, value, expected) => {
        const { getByRole } = render(<IntegerInput min={min} max={max} />);
        const input = getByRole("textbox");
        await userEvent.type(input, value.toString());
        expect(input).toHaveValue(expected);
      }
    );
  });

  describe("数値以外の文字は入力できないこと", () => {
    it.each([
      ["a", ""],
      ["a1", "1"],
      ["1.", "1"],
    ])(`%sを入力したときは%sになる`, async (value, expected) => {
      const { getByRole } = render(<IntegerInput min={0} max={10} />);
      const input = getByRole("textbox") as HTMLInputElement;
      await userEvent.type(input, value);
      expect(input).toHaveValue(expected);
    });
  });

  it("全角数字は半角数字に変換される", async () => {
    const { getByRole } = render(<IntegerInput min={-200} max={10} />);
    const input = getByRole("textbox") as HTMLInputElement;
    await userEvent.type(input, "ー１２３");
    expect(input).toHaveValue("-123");
  });
});
