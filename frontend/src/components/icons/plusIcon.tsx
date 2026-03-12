import { THEME_COLORS } from "@/consts/color";
import React from "react";

interface Props {
  color?: string;
  className: string;
}

export const PlusIcon = ({
  color = THEME_COLORS.button,
  className,
}: Props): JSX.Element => {
  return (
    <svg
      className={`${className}`}
      width="106"
      height="106"
      viewBox="0 0 106 106"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <g filter="url(#filter0_dd_0_1)">
        <circle cx="53" cy="49" r="40" fill={color} />
      </g>
      <path
        d="M51.1648 50.8367H38.6001V47.1317H51.1648L51.1648 34.6001H54.867L54.867 47.1317H67.4001L67.4001 50.8367H54.867V63.4001H51.1648V50.8367Z"
        fill="white"
      />
      <defs>
        <filter
          id="filter0_dd_0_1"
          x="0"
          y="0"
          width="106"
          height="106"
          filterUnits="userSpaceOnUse"
          colorInterpolationFilters="sRGB"
        >
          <feFlood floodOpacity="0" result="BackgroundImageFix" />
          <feColorMatrix
            in="SourceAlpha"
            type="matrix"
            values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
            result="hardAlpha"
          />
          <feMorphology
            radius="1"
            operator="erode"
            in="SourceAlpha"
            result="effect1_dropShadow_0_1"
          />
          <feOffset dx="-1" dy="-1" />
          <feGaussianBlur stdDeviation="0.5" />
          <feComposite in2="hardAlpha" operator="out" />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 1 0"
          />
          <feBlend
            mode="normal"
            in2="BackgroundImageFix"
            result="effect1_dropShadow_0_1"
          />
          <feColorMatrix
            in="SourceAlpha"
            type="matrix"
            values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0"
            result="hardAlpha"
          />
          <feMorphology
            radius="1"
            operator="dilate"
            in="SourceAlpha"
            result="effect2_dropShadow_0_1"
          />
          <feOffset dy="4" />
          <feGaussianBlur stdDeviation="6" />
          <feComposite in2="hardAlpha" operator="out" />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0.344053 0 0 0 0 0.408809 0 0 0 0 0.575326 0 0 0 0.5 0"
          />
          <feBlend
            mode="normal"
            in2="effect1_dropShadow_0_1"
            result="effect2_dropShadow_0_1"
          />
          <feBlend
            mode="normal"
            in="SourceGraphic"
            in2="effect2_dropShadow_0_1"
            result="shape"
          />
        </filter>
      </defs>
    </svg>
  );
};
