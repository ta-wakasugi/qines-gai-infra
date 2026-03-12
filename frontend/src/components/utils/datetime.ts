/**
 * 現在の日時を指定されたフォーマットで取得する
 * @param local - ロケール設定（デフォルト: "ja-JP"）
 * @param timeZone - タイムゾーン設定（デフォルト: "Asia/Tokyo"）
 * @returns フォーマットされた日時文字列
 */
export const getNowDateTimeString = (
  local: string = "ja-JP",
  timeZone: string = "Asia/Tokyo"
) =>
  new Date()
    .toLocaleString(local, {
      timeZone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })
    .replace(/\/|:| /g, "");

/**
 * 日時文字列を表示用にフォーマットする
 * @param dateTime - 日時文字列
 * @returns フォーマットされた日時文字列
 */
export const formatDateTime = (dateTime: string) => {
  const [date, time] = dateTime.split(" ");
  if (!time) return date;
  const [hour, minute] = time.split(":");
  return `${date} ${hour}:${minute}`;
};
