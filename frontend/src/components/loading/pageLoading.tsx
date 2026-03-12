"use client";
import { useLoading } from "@/hooks/useLoading";
import "./pageLoading.css";

type Props = {
  text: string;
  className?: string;
};

/**
 * 画面ローディングコンポーネント
 * @param props - コンポーネントのプロパティ
 * @param props.text - 表示するテキスト
 * @param props.className - スタイルクラス名
 * @returns ローディングのJSX要素
 */
export default function PageLoading(props: Props) {
  const { isLoading } = useLoading();

  return (
    <>
      {isLoading && (
        <div
          className={`z-30 fixed inset-0 bg-[#D8DFE3B2] opacity-70 text-action-blue rounded-lg shadow-xl flex flex-col justify-center items-center ${props.className}`}
        >
          <div className="loader border-action-blue"></div>
          <span className="mt-4 text-center whitespace-pre-wrap break-words">
            {props.text}
          </span>
        </div>
      )}
    </>
  );
}
