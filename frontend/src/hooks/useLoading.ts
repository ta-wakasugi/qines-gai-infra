"use client";
import { atom, useAtom } from "jotai";

const isLoadingAtom = atom<boolean>(false);
const loadingTextAtom = atom<string>("");

/**
 * ローディング状態を管理するカスタムフック
 * @returns {Object} ローディング状態と操作関数を含むオブジェクト
 * @property {boolean} isLoading - ローディング状態
 * @property {Function} showLoading - ローディングを表示する関数
 * @property {Function} hideLoading - ローディングを非表示にする関数
 */
export const useLoading = () => {
  const [isLoading, setIsLoading] = useAtom(isLoadingAtom);
  const [loadingText, setLoadingText] = useAtom(loadingTextAtom);

  const showLoading = () => {
    setIsLoading(true);
  };
  const hideLoading = () => {
    setIsLoading(false);
    setLoadingText("");
  };
  return {
    isLoading,
    showLoading,
    hideLoading,
    loadingText,
    setLoadingText,
  };
};
