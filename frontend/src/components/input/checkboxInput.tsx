interface CheckBoxProps {
  checked: boolean;
  label: string;
  onClick: () => void;
}

/**
 * チェックボックス入力コンポーネント
 * @param props - コンポーネントのプロパティ
 * @param props.checked - チェック状態
 * @param props.label - チェックボックスのラベル
 * @param props.onClick - クリック時のコールバック関数
 * @returns チェックボックスのJSX要素
 */
export const CheckboxInput = ({ checked, onClick, label }: CheckBoxProps) => {
  return (
    <div
      role="checkbox"
      aria-label={label}
      aria-checked={checked}
      className={`w-5 h-5 rounded border-2 flex items-center justify-center cursor-pointer transition-all duration-200 ease-in-out ${
        checked
          ? "bg-action-blue border-action-blue"
          : "bg-white border-light-gray hover:border-action-blue"
      }`}
      onClick={onClick}
    >
      {checked && (
        <svg
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect
            x="0.5"
            y="0.5"
            width="17"
            height="17"
            rx="3.5"
            fill="#161DDA"
            stroke="#161DDA"
          />
          <path d="M4 8L8 12.5L14 5" stroke="white" />
        </svg>
      )}
    </div>
  );
};
