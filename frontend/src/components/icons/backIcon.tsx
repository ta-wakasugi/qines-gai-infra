import PropTypes from "prop-types";
import React from "react";

interface Props {
  color?: string;
  className?: string;
}

export const BackIcon = ({ color, className }: Props): JSX.Element => {
  return (
    <svg
      className={`${className}`}
      fill="none"
      height="36"
      viewBox="0 0 36 36"
      width="36"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path d="M22 26L14 18L22 10" stroke={color} strokeWidth="1.6" />
    </svg>
  );
};

BackIcon.propTypes = {
  color: PropTypes.string,
};
