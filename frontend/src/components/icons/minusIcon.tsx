import { THEME_COLORS } from "@/consts/color";

interface Props {
  className: string;
  color?: string;
}

export const MinusIcon = ({ className, color = THEME_COLORS.button }: Props) => {
  return (
    <svg
      className={`${className}`}
      fill="none"
      height="30"
      viewBox="0 0 32 30"
      width="32"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        cx="15.5"
        cy="15"
        r="14.4"
        stroke={color}
        strokeWidth="1.2"
        transform="rotate(-180 15.5 15)"
      />

      <path d="M8.5 15H22.5" stroke={color} strokeWidth="1.2" />
    </svg>
  );
};
