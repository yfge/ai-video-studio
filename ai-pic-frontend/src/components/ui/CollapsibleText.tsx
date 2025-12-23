"use client";

import { useMemo, useState } from "react";

type CollapsibleLineClamp = 2 | 3 | 4;

interface CollapsibleTextProps {
  text: string;
  collapsedLines?: CollapsibleLineClamp;
  className?: string;
}

const clampClassMap: Record<CollapsibleLineClamp, string> = {
  2: "line-clamp-2",
  3: "line-clamp-3",
  4: "line-clamp-4",
};

export function CollapsibleText({
  text,
  collapsedLines = 3,
  className,
}: CollapsibleTextProps) {
  const [expanded, setExpanded] = useState(false);
  const trimmed = text.trim();

  const shouldClamp = useMemo(() => {
    const lineCount = trimmed.split(/\r?\n/).length;
    return trimmed.length > 140 || lineCount > collapsedLines;
  }, [collapsedLines, trimmed]);

  if (!trimmed) {
    return null;
  }

  const clampClass = clampClassMap[collapsedLines] || clampClassMap[3];
  const textClassName = [
    "text-gray-700",
    "whitespace-pre-wrap",
    !expanded && shouldClamp ? clampClass : "",
    className || "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div>
      <p className={textClassName}>{trimmed}</p>
      {shouldClamp ? (
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="mt-2 text-sm text-blue-600 hover:text-blue-700"
          aria-expanded={expanded}
        >
          {expanded ? "收起" : "展开"}
        </button>
      ) : null}
    </div>
  );
}
