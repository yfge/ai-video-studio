import type {
  NovelChapterLength,
  NovelChapterLengthOverrides,
  NovelLengthRange,
} from "@/utils/api/types";

export const DEFAULT_CUSTOM_LENGTH: NovelLengthRange = {
  min_chars: 3000,
  target_chars: 4000,
  max_chars: 5000,
};

export function validateLengthRange(range: NovelLengthRange) {
  const values = [range.min_chars, range.target_chars, range.max_chars];
  if (!values.every((value) => Number.isInteger(value) && value > 0)) {
    return "最小、目标和最大字数必须是正整数";
  }
  if (
    range.min_chars > range.target_chars ||
    range.target_chars > range.max_chars
  ) {
    return "字数范围必须满足最小值 ≤ 目标值 ≤ 最大值";
  }
  return null;
}

export function chapterLength(
  position: number,
  defaults: NovelLengthRange,
  overrides: NovelChapterLengthOverrides,
): NovelChapterLength {
  const override = overrides[String(position)];
  return override
    ? { ...override, source: "chapter_override" }
    : { ...defaults, source: "profile_default" };
}

export function plannedLengthTotals(
  positions: number[],
  defaults: NovelLengthRange,
  overrides: NovelChapterLengthOverrides,
) {
  return positions.reduce(
    (totals, position) => {
      const length = chapterLength(position, defaults, overrides);
      totals.min_chars += length.min_chars;
      totals.target_chars += length.target_chars;
      totals.max_chars += length.max_chars;
      return totals;
    },
    { min_chars: 0, target_chars: 0, max_chars: 0 },
  );
}

export function validateLengthOverrides(
  overrides: NovelChapterLengthOverrides,
) {
  for (const [position, range] of Object.entries(overrides)) {
    const error = validateLengthRange(range);
    if (error) return `第 ${position} 章：${error}`;
  }
  return null;
}

export function applyRangeToChapters(
  positions: number[],
  overrides: NovelChapterLengthOverrides,
  range: NovelLengthRange,
  onlyMissing = false,
) {
  return positions.reduce<NovelChapterLengthOverrides>(
    (next, position) => {
      const key = String(position);
      if (!onlyMissing || !next[key]) next[key] = { ...range };
      return next;
    },
    { ...overrides },
  );
}

export const formatCharacterCount = (value: number) =>
  new Intl.NumberFormat("zh-CN").format(value);
