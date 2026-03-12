import { toHalfWidth } from "./toHalfWidth";

describe("toHalfWidth", () => {
  it.each([
    [
      "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ",
      "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    ],
    [
      "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ",
      "abcdefghijklmnopqrstuvwxyz",
    ],
    ["０１２３４５６７８９", "0123456789"],
  ])("全角文字が半角文字に変換される", (input, expected) => {
    expect(toHalfWidth(input)).toBe(expected);
  });
});
