import type { SVGProps } from "react";

export type OperatorNavIconName =
  | "workspace"
  | "ip"
  | "stories"
  | "environments"
  | "tasks"
  | "users"
  | "stats"
  | "settings";

export function OperatorShellNavIcon({
  name,
  ...props
}: SVGProps<SVGSVGElement> & { name: OperatorNavIconName }) {
  const commonProps: SVGProps<SVGSVGElement> = {
    "aria-hidden": true,
    fill: "none",
    focusable: false,
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeWidth: 1.8,
    viewBox: "0 0 24 24",
    ...props,
  };

  switch (name) {
    case "workspace":
      return (
        <svg {...commonProps}>
          <path d="M4 5.5h7v6H4z" />
          <path d="M13 5.5h7v13h-7z" />
          <path d="M4 13.5h7v5H4z" />
        </svg>
      );
    case "ip":
      return (
        <svg {...commonProps}>
          <circle cx="12" cy="8.2" r="3.2" />
          <path d="M5.8 19c.8-3.2 3.1-5 6.2-5s5.4 1.8 6.2 5" />
          <path d="M4.5 4.5h15v15h-15z" />
        </svg>
      );
    case "stories":
      return (
        <svg {...commonProps}>
          <path d="M5 5.5h6.2A2.8 2.8 0 0 1 14 8.3v10.2H7.8A2.8 2.8 0 0 0 5 21.3z" />
          <path d="M19 5.5h-5a2.8 2.8 0 0 0-2.8 2.8v10.2h5A2.8 2.8 0 0 1 19 21.3z" />
          <path d="M8 9h2.2" />
          <path d="M15 9h1.2" />
        </svg>
      );
    case "environments":
      return (
        <svg {...commonProps}>
          <path d="M4.5 5h15v14h-15z" />
          <path d="m6.8 16.5 3.7-4.2 2.8 3 1.7-2 2.2 3.2" />
          <circle cx="16.6" cy="8.4" r="1.3" />
        </svg>
      );
    case "tasks":
      return (
        <svg {...commonProps}>
          <path d="M9.2 6.8h9.3" />
          <path d="M9.2 12h9.3" />
          <path d="M9.2 17.2h9.3" />
          <path d="m4.8 6.8 1 1 2-2.1" />
          <path d="m4.8 12 1 1 2-2.1" />
          <path d="m4.8 17.2 1 1 2-2.1" />
        </svg>
      );
    case "users":
      return (
        <svg {...commonProps}>
          <circle cx="9.5" cy="8.5" r="3" />
          <path d="M4.5 18.5c.7-3 2.5-4.5 5-4.5s4.3 1.5 5 4.5" />
          <path d="M15 6.2a2.7 2.7 0 0 1 0 5.1" />
          <path d="M15.8 14.2c2 .4 3.2 1.8 3.7 4.3" />
        </svg>
      );
    case "stats":
      return (
        <svg {...commonProps}>
          <path d="M5 19V5" />
          <path d="M5 19h14" />
          <path d="M8.2 15v-3.8" />
          <path d="M12 15V8" />
          <path d="M15.8 15v-5.2" />
        </svg>
      );
    case "settings":
      return (
        <svg {...commonProps}>
          <circle cx="12" cy="12" r="3.2" />
          <path d="M12 4.8V3" />
          <path d="M12 21v-1.8" />
          <path d="m6.9 6.9-1.3-1.3" />
          <path d="m18.4 18.4-1.3-1.3" />
          <path d="M4.8 12H3" />
          <path d="M21 12h-1.8" />
          <path d="m6.9 17.1-1.3 1.3" />
          <path d="m18.4 5.6-1.3 1.3" />
        </svg>
      );
  }
}
