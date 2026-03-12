"use client";
import { atom, useAtom } from "jotai";

const messageAtom = atom<string>("");
const DEFAULT_DISPLAY_TIME = 3000; // スナックバーを表示するデフォルト時間:3秒

/**
 * スナックバーカスタムフック
 * @returns {Object} スナックバーに関する値とメソッド
 * @property {string} snackbarMessage - 現在のスナックバーメッセージ
 * @property {Function} showSnackbar - スナックバーを表示するメソッド
 * @property {Function} hiddenSnackbar - スナックバーを非表示にするメソッド
 */
export const useSnackbar = () => {
  const [snackbarMessage, setSnackbarMessage] = useAtom(messageAtom);
  /**
   * スナックバーを表示し、指定時間後に非表示にする
   * @param message スナックバー表示メッセージ
   * @param defaultClose 表示した後にデフォルトで非表示にするか
   * @param displayTime 非表示にするまでの秒数
   */
  const showSnackbar = async (
    message: string,
    defaultClose: boolean = true,
    displayTime: number = DEFAULT_DISPLAY_TIME
  ) => {
    setSnackbarMessage(message);
    if (defaultClose) {
      await new Promise((resolve) => setTimeout(resolve, displayTime));
      hiddenSnackbar();
    }
  };
  /**
   * スナックバーのメッセージをリセットし非表示にする
   */
  const hiddenSnackbar = () => {
    setSnackbarMessage("");
  };

  return {
    snackbarMessage,
    showSnackbar,
    hiddenSnackbar,
  };
};
