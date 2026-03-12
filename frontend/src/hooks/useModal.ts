"use client";
import { useState } from "react";

/**
 * モーダルの表示・非表示を制御するカスタムフック
 * @returns {Object} モーダル制御に関する値とメソッド
 * @property {boolean} isOpen - モーダルの表示状態
 * @property {Function} showModal - モーダルを表示するメソッド
 * @property {Function} hideModal - モーダルを非表示にするメソッド
 */
export const useModal = () => {
  const [isOpen, setIsOpen] = useState(false);
  const showModal = (
    event:
      | React.FormEvent<HTMLFormElement>
      | React.MouseEvent<HTMLButtonElement, MouseEvent>
  ) => {
    event.preventDefault(); // formタグでの遷移をキャンセル
    setIsOpen(true);
  };
  const hideModal = () => {
    setIsOpen(false);
  };
  return {
    isOpen,
    showModal,
    hideModal,
  };
};
