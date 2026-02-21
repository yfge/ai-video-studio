import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";

export default [
  ...coreWebVitals,
  ...typescript,
  {
    name: "legacy-api-import-guard",
    files: ["src/**/*.{ts,tsx,js,jsx}"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          paths: [
            {
              name: "@/utils/api",
              message:
                "Legacy api.ts entrypoint is frozen. Use '@/utils/api/endpoints', '@/utils/api/types', or '@/utils/api/client' instead.",
            },
            {
              name: "@/utils/api.ts",
              message:
                "Legacy api.ts entrypoint is frozen. Use '@/utils/api/endpoints', '@/utils/api/types', or '@/utils/api/client' instead.",
            },
          ],
        },
      ],
    },
  },
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
