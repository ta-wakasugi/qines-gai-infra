import { formatDateTime, getNowDateTimeString } from "./datetime";

describe("getNowDateTimeString", () => {
  beforeAll(() => {
    // テスト中の時刻を固定
    jest.useFakeTimers();
    jest.setSystemTime(new Date("2024-01-02T10:20:30"));
  });

  afterAll(() => {
    // テスト後に元の時刻に戻す
    jest.useRealTimers();
  });

  test("getNowDateTimeStringは現在時刻を取得する", () => {
    const result = getNowDateTimeString();
    expect(result).toBe("20240102102030");
  });

  test.todo("異なるロケール/TZで正しい文字列を返す");

  it("日付フォーマット:時刻ありの場合、分まで表示となること", () => {
    const testDate = "2024/12/10 11:44:22.785052";
    const result = formatDateTime(testDate);
    const expected = "2024/12/10 11:44";
    expect(result).toBe(expected);
  });

  it("日付フォーマット:時刻なしの場合、日付だけ表示となること", () => {
    const testDate = "2024/12/10";
    const result = formatDateTime(testDate);
    expect(result).toBe(testDate);
  });
});
