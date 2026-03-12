import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "action-blue": "#161dda",
        "pale-blue": "#9facb8",
        "chat-area": "#ffffff99",
        "light-gray": "#d8dfdf",
        "orange-alert": "#FF3519",
      },
    },
  },
  plugins: [],
};
export default config;
