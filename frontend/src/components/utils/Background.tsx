type Props = {
  className?: string;
};

/**
 * 背景コンポーネント
 * @param props - コンポーネントのプロパティ
 * @param props.className - スタイルクラス名
 * @returns 背景のJSX要素
 */
export default function Background({ className }: Props) {
  return (
    <>
      <div
        className={`absolute inset-0 z-0 top-1 bottom-1 right-1 bg-white bg-opacity-40 rounded-lg shadow-xl ${className}`}
      />
    </>
  );
}
