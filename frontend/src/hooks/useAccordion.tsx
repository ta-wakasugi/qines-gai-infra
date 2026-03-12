"use client";

import { ArrowDownIcon } from "@/components/icons/arrowDownIcon";
import { ArrowUpIcon } from "@/components/icons/arrowUpIcon";
import { useState } from "react";

/**
 * Accordionコンポーネントのカスタムフック
 * @param {boolean} isDefaultOpen - デフォルトで開いているかどうか
 * @param {string} buttonSize - アコーディオンのボタンサイズ
 * @returns {Object} アコーディオンの開閉状態と操作関数
 * @property {boolean} isOpen - アコーディオンの開閉状態
 * @property {ReactNode} triggerIcon - 開閉トリガーのアイコン
 * @property {Function} toggleAccordion - アコーディオンの開閉を切り替える関数
 */
export const useAccordion = (isDefaultOpen: boolean, buttonSize: string = "5") => {
  const [isOpen, setIsOpen] = useState(isDefaultOpen);
  const buttonClassName = `w-${buttonSize} h-${buttonSize}`;
  const triggerIcon = isOpen ? (
    <ArrowUpIcon className={buttonClassName} />
  ) : (
    <ArrowDownIcon className={buttonClassName} />
  );

  /**
   * アコーディオンの開閉を切り替える関数
   */
  const toggleAccordion = () => {
    setIsOpen(!isOpen);
  };

  return {
    isOpen,
    triggerIcon,
    toggleAccordion,
  };
};
