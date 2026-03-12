"use client";

import { THEME_COLORS } from "@/consts/color";
import { atom, useAtom } from "jotai";

const buttonDisabledAtom = atom(false);

/**
 * ボタンの無効化状態を制御するカスタムフック
 * @returns {Object} ボタンの無効化制御に関する値とメソッド
 * @property {boolean} commonButtonDisabled - ボタンの無効化状態
 * @property {Function} setCommonButtonDisabled - ボタンの無効化状態を設定するメソッド
 * @property {string} buttonColor - ボタンの色（無効時は異なる色を返す）
 */
export const useButtonDisabled = () => {
  const [commonButtonDisabled, setCommonButtonDisabled] = useAtom(buttonDisabledAtom);
  const buttonColor = commonButtonDisabled
    ? THEME_COLORS.buttonDisabled
    : THEME_COLORS.button;

  return {
    commonButtonDisabled,
    setCommonButtonDisabled,
    buttonColor,
  };
};
