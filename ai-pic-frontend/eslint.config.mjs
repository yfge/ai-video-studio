import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";

export default [
  ...coreWebVitals,
  ...typescript,
  {
    name: "project-overrides",
    rules: {
      "react-hooks/set-state-in-effect": "off",
    },
  },
  {
    name: "tests-overrides",
    files: ["tests/**/*.{ts,tsx,js,jsx}"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
];
