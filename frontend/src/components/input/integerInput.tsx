import { toHalfWidth } from "@/utils/toHalfWidth";
import { useEffect, useState } from "react";

type Props = {
  min: number;
  max: number;
  defaultValue?: string;
  className?: string;
};

/**
 * 整数入力フィールドコンポーネント
 * @param props - コンポーネントのプロパティ
 * @param props.min - 入力可能な最小値
 * @param props.max - 入力可能な最大値
 * @param props.defaultValue - デフォルト値（初期値: ""）
 * @param props.className - スタイルクラス名
 * @returns 整数入力フィールドのJSX要素
 */
const IntegerInput = ({ min, max, defaultValue = "", className }: Props) => {
  const [inputValue, setInputValue] = useState(defaultValue);
  useEffect(() => {
    setInputValue(defaultValue);
  }, [defaultValue]);

  /**
   * 入力値の変更を処理するハンドラー
   * @param e - 入力イベント
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // 半角数字または全角数字または"-"ではない場合はe.target.valueを更新しない
    if (!/^[0-9０-９-ー]+$/.test(e.target.value)) {
      e.target.value = e.target.value.replace(/[^0-9０-９-ー]/g, "");
    }
    // 全角数字を半角数字に変換
    e.target.value = toHalfWidth(e.target.value);

    // 最小値未満の場合は更新しない
    if (parseInt(e.target.value, 10) < min) {
      e.target.value = e.target.value.slice(0, -1);
    }
    // 最大値を超える場合は更新しない
    if (parseInt(e.target.value, 10) > max) {
      e.target.value = e.target.value.slice(0, -1);
    }
    setInputValue(e.target.value);
  };
  return (
    <input
      type="text"
      name="value"
      min={min}
      max={max}
      step="1"
      value={inputValue}
      className={`border ${className}`}
      onChange={handleChange}
    />
  );
};

export default IntegerInput;
