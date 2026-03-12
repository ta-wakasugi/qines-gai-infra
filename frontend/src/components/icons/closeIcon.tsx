interface Props {
  color?: string;
  className?: string;
}

export const CloseIcon = ({ color, className }: Props): JSX.Element => {
  return (
    <svg
      className={`${className}`}
      width="22"
      height="22"
      viewBox="0 0 22 22"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M11 0.999999C5.47715 0.999999 1 5.47715 1 11C1 16.5228 5.47715 21 11 21C16.5228 21 21 16.5228 21 11C21 5.47715 16.5228 1 11 0.999999ZM11 -9.61651e-07C4.92487 -1.49276e-06 1.49276e-06 4.92487 9.61651e-07 11C4.30546e-07 17.0751 4.92487 22 11 22C17.0751 22 22 17.0751 22 11C22 4.92487 17.0751 -4.30546e-07 11 -9.61651e-07Z"
        fill={color}
      />
      <path
        d="M7.63348 15L7 14.3665L10.3665 11L7 7.63348L7.63348 7L11 10.3665L14.3665 7L15 7.63348L11.6335 11L15 14.3665L14.3665 15L11 11.6335L7.63348 15Z"
        fill={color}
      />
    </svg>
  );
};
