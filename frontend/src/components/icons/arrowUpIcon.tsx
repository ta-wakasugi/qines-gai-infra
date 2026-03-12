interface Props {
  className: string;
}

export const ArrowUpIcon = ({ className }: Props): JSX.Element => {
  return (
    <svg
      className={`${className}`}
      data-testid="arrowUp"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle
        cx="12"
        cy="12"
        r="11.5"
        transform="rotate(-180 12 12)"
        stroke="#A5AEAC"
      />
      <path d="M7.2002 14.3996L12.0002 9.59961L16.8002 14.3996" stroke="#A5AEAC" />
    </svg>
  );
};
