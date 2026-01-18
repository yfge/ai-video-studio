import type { Script } from "@/utils/api/types";

const parseVersion = (value: string) => {
  const normalized = (value || "").trim().replace(/^v/i, "");
  const parsed = Number.parseFloat(normalized);
  return Number.isFinite(parsed) ? parsed : null;
};

const parseTime = (value: string) => {
  const parsed = Date.parse(value || "");
  return Number.isFinite(parsed) ? parsed : null;
};

export const sortScriptsNewestFirst = (scripts: Script[]) => {
  return [...scripts].sort((a, b) => {
    const versionA = parseVersion(a.version);
    const versionB = parseVersion(b.version);
    if (versionA !== null && versionB !== null && versionA !== versionB) {
      return versionB - versionA;
    }

    const timeA = parseTime(a.created_at);
    const timeB = parseTime(b.created_at);
    if (timeA !== null && timeB !== null && timeA !== timeB) {
      return timeB - timeA;
    }

    return b.id - a.id;
  });
};
