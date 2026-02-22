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
            {
              name: "@/utils/api/index",
              message:
                "Legacy api index entrypoint is frozen. Import from '@/utils/api/endpoints', '@/utils/api/types', or '@/utils/api/client' directly.",
            },
            {
              name: "@/utils/api/index.ts",
              message:
                "Legacy api index entrypoint is frozen. Import from '@/utils/api/endpoints', '@/utils/api/types', or '@/utils/api/client' directly.",
            },
            {
              name: "@/utils/api/episodeCharacters",
              message:
                "Legacy episodeCharacters entrypoint was split. Import endpoints from '@/utils/api/endpoints' and types from '@/utils/api/types'.",
            },
            {
              name: "@/utils/api/episodeCharacters.ts",
              message:
                "Legacy episodeCharacters entrypoint was split. Import endpoints from '@/utils/api/endpoints' and types from '@/utils/api/types'.",
            },
          ],
          patterns: [
            {
              group: [
                "utils/api",
                "utils/api.ts",
                "utils/api/index",
                "utils/api/index.ts",
                "./utils/api",
                "./utils/api.ts",
                "./utils/api/index",
                "./utils/api/index.ts",
                "../utils/api",
                "../utils/api.ts",
                "../utils/api/index",
                "../utils/api/index.ts",
                "../../utils/api",
                "../../utils/api.ts",
                "../../utils/api/index",
                "../../utils/api/index.ts",
                "../../../utils/api",
                "../../../utils/api.ts",
                "../../../utils/api/index",
                "../../../utils/api/index.ts",
                "../../../../utils/api",
                "../../../../utils/api.ts",
                "../../../../utils/api/index",
                "../../../../utils/api/index.ts",
                "../../../../../utils/api",
                "../../../../../utils/api.ts",
                "../../../../../utils/api/index",
                "../../../../../utils/api/index.ts",
                "../../../../../../utils/api",
                "../../../../../../utils/api.ts",
                "../../../../../../utils/api/index",
                "../../../../../../utils/api/index.ts",
              ],
              message:
                "Legacy api.ts/index entrypoints are frozen. Import from split modules under utils/api/endpoints, utils/api/types, or utils/api/client.",
            },
            {
              group: ["@/utils/api/endpoints/*", "@/utils/api/types/*"],
              message:
                "Use barrel imports from '@/utils/api/endpoints' and '@/utils/api/types' instead of deep module paths.",
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
