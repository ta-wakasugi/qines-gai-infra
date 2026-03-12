/**
 * 全角英数字とハイフンを半角に変換します
 * @param str - 変換対象の文字列
 * @returns 半角に変換された文字列
 * @example
 * toHalfWidth("ＡＢＣ１２３ー") // => "ABC123-"
 */
export const toHalfWidth = (str: string) =>
  str.replace(/[Ａ-Ｚａ-ｚ０-９ー]/g, (s) => {
    if (s === "ー") return "-";
    return String.fromCharCode(s.charCodeAt(0) - 0xfee0);
  });
