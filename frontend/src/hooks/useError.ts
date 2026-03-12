"use client";
import { atom, useAtom } from "jotai";

const errorMessageAtom = atom<string>("");

/**
 * エラーメッセージの表示を制御するカスタムフック
 * @returns {Object} エラー制御に関する値とメソッド
 * @property {string} errorMessage - 現在のエラーメッセージ
 * @property {Object} errorTemplate - 一般的なエラーメッセージのテンプレート
 * @property {Function} showError - エラーメッセージを表示するメソッド
 * @property {Function} hiddenError - エラーメッセージを非表示にするメソッド
 */
export const useError = () => {
  const [errorMessage, setErrorMessage] = useAtom(errorMessageAtom);
  // エラーメッセージのテンプレート
  const errorTemplate = {
    api: "処理に失敗しました。もう一度やり直してください。",
    user: "入力内容に誤りがあります。",
  };
  const showError = (message: string) => {
    setErrorMessage(message);
  };
  const hiddenError = () => {
    setErrorMessage("");
  };

  return {
    errorMessage,
    errorTemplate,
    showError,
    hiddenError,
  };
};
