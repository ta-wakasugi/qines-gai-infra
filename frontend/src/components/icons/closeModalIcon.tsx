interface Props {
  color?: string;
  className?: string;
}

export const CloseModalIcon = ({ color, className }: Props): JSX.Element => {
  return (
    <svg
      className={`${className}`}
      width="26"
      height="27"
      viewBox="0 0 26 27"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      data-testid="close-modal-icon"
    >
      <mask
        id="mask0_50_1282"
        maskUnits="userSpaceOnUse"
        x="0"
        y="0"
        width="26"
        height="27"
      >
        <rect y="0.5" width="26" height="26" fill="#D9D9D9" />
      </mask>
      <g mask="url(#mask0_50_1282)">
        <path
          d="M6.93355 20.7082L5.79199 19.5666L11.8587 13.5L5.79199 7.43331L6.93355 6.29175L13.0002 12.3584L19.0669 6.29175L20.2085 7.43331L14.1418 13.5L20.2085 19.5666L19.0669 20.7082L13.0002 14.6415L6.93355 20.7082Z"
          fill={color}
        />
      </g>
    </svg>
  );
};
