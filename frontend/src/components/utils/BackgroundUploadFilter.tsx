type Props = {
  isDisplay: boolean;
  text: string;
  className?: string;
};

/**
 * アップロード中の背景フィルターコンポーネント
 * @param props - コンポーネントのプロパティ
 * @param props.isDisplay - フィルターの表示状態
 * @param props.text - 表示するテキスト
 * @param props.className - スタイルクラス名
 * @returns 背景フィルターのJSX要素
 */
export default function BackgroundUploadFilter(props: Props) {
  return (
    <>
      {props.isDisplay && (
        <div
          className={`z-20 fixed inset-0 bg-gray-200 opacity-90 text-action-blue rounded-lg shadow-xl flex justify-center items-center ${props.className}`}
        >
          <span className="text-center whitespace-pre-wrap break-words">
            {props.text}
          </span>
        </div>
      )}
    </>
  );
}
