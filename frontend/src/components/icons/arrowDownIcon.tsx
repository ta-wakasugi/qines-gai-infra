interface Props {
  className: string;
}

export const ArrowDownIcon = ({ className }: Props): JSX.Element => {
  return (
    <svg
      className={`${className}`}
      data-testid="arrowDown"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="12" cy="12" r="11.5" stroke="#A5AEAC" />
      <path d="M7.2002 9.59961L12.0002 14.3996L16.8002 9.59961" stroke="#A5AEAC" />
    </svg>
  );
};
