import { ReactNode } from "react";

type Prop = {
  children: ReactNode;
  isOpen: boolean;
};

/**
 * ベースモーダルコンポーネント
 * @param props - モーダルのプロパティ
 * @param props.children - モーダルの内容
 * @param props.isOpen - モーダルの表示状態
 * @returns モーダルのJSX要素
 */
export const BaseModal = ({ children, isOpen }: Prop) => {
  if (!isOpen) {
    return null;
  }
  return (
    <div className="fixed z-20 inset-0 overflow-y-auto">
      <div className="flex items-center justify-center  min-h-screen">
        <div className="fixed inset-0 bg-gray-200 opacity-90" aria-hidden="true"></div>
        {children}
      </div>
    </div>
  );
};
