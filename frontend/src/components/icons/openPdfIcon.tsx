import { THEME_COLORS } from "@/consts/color";

interface Props {
  className?: string;
  color?: string;
}

export const OpenPdfIcon = ({ className, color = THEME_COLORS.button }: Props) => {
  return (
    <svg
      className={`${className}`}
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M9.99967 18.333C14.602 18.333 18.333 14.602 18.333 9.99967C18.333 5.3973 14.602 1.66634 9.99967 1.66634C5.3973 1.66634 1.66634 5.3973 1.66634 9.99967C1.66634 14.602 5.3973 18.333 9.99967 18.333ZM9.99967 19.1663C15.0623 19.1663 19.1663 15.0623 19.1663 9.99967C19.1663 4.93706 15.0623 0.833008 9.99967 0.833008C4.93706 0.833008 0.833008 4.93706 0.833008 9.99967C0.833008 15.0623 4.93706 19.1663 9.99967 19.1663Z"
        fill={color}
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12.9167 7.08333H7.5V6.25H13.75V12.5H12.9167V7.08333Z"
        fill={color}
      />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M13.0383 6.37201L6.37168 13.0387L6.96094 13.6279L13.6276 6.96126L13.0383 6.37201Z"
        fill={color}
      />
    </svg>
  );
};
