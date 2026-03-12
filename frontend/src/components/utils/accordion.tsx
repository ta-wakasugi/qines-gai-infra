"use client";
import { useAccordion } from "@/hooks/useAccordion";
import { ReactNode } from "react";

type AccordionProps = {
  title: string;
  children: ReactNode;
};

/**
 * アコーディオンコンポーネント
 * @param props - コンポーネントのプロパティ
 * @param props.title - アコーディオンのタイトル
 * @param props.children - アコーディオンの内容
 * @returns アコーディオンのJSX要素
 */
export default function Accordion({ title, children }: AccordionProps) {
  const { isOpen, triggerIcon, toggleAccordion } = useAccordion(false);

  return (
    <>
      <div className="w-full">
        <hr className="border mb-3" />
        <div className="flex items-center justify-between w-full">
          <button onClick={toggleAccordion} className="flex items-center text-left">
            {triggerIcon}
            <span className="ml-3 text-gray-600">{title}</span>
          </button>
        </div>
        {isOpen && <div>{children}</div>}
      </div>
    </>
  );
}
