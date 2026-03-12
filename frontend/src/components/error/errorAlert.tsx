"use client";
import { useError } from "@/hooks/useError";

/**
 * エラーアラートコンポーネント
 * エラーメッセージを表示し、閉じることができるアラートを提供する
 * @returns エラーアラートのJSX要素、またはエラーがない場合はnull
 */
export const ErrorAlert = () => {
  const { errorMessage, hiddenError } = useError();
  if (!errorMessage) return null;

  /**
   * アラートを閉じる処理を行うハンドラー
   */
  const closeAlert = () => {
    hiddenError();
  };

  return (
    // TODO 仮でスタイルを適用
    <div className="flex items-center justify-between bg-red-50 border border-red-200 text-gray-600 px-4 py-5 rounded-md shadow-md fixed right-0 left-0 top-24 z-30 max-w-lg m-auto">
      <div className="flex items-center">
        <div className="mr-3"></div>
        <div>
          <p className="font-bold">エラー</p>
          <p data-testid="error">{errorMessage}</p>
        </div>
      </div>
      <button className="text-3xl" onClick={closeAlert}>
        ×
      </button>
    </div>
  );
};
