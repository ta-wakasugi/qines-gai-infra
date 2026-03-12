interface Props {
  color?: string;
  className?: string;
}

export const SendIcon = ({ color = "#A5ACAE", className }: Props) => {
  return (
    <svg
      className={`${className}`}
      width="20"
      height="18"
      viewBox="0 0 20 18"
      fill={`${color}`}
      xmlns="http://www.w3.org/2000/svg"
    >
      <g clipPath="url(#clip0_1388_6404)">
        <path
          d="M0 17.182V0.818359L19.2 9.00018L0 17.182ZM1.6733 14.6428L14.8924 9.00018L1.6733 3.35754V7.52435L7.72284 9.00018L1.6733 10.476V14.6428Z"
          fill={`${color}`}
        />
      </g>
      <defs>
        <clipPath id="clip0_1388_6404">
          <rect width="20" height="18" fill="white" />
        </clipPath>
      </defs>
    </svg>
  );
};
