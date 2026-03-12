import React from "react";

type Prop = {
  children: React.ReactNode;
  className?: string;
  id?: string;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  disabled: boolean;
};

/** 保存ボタンコンポーネント */
export const SaveButton = ({ children, className, id, onClick, disabled }: Prop) => {
  const buttonColor = disabled ? "bg-light-gray" : "bg-action-blue";
  return (
    <button
      className={`${buttonColor} text-white rounded-lg py-4 text-lg ${className}`}
      id={id}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};
