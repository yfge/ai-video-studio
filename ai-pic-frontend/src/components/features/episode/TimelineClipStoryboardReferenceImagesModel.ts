import type {
  Environment,
  EpisodeCharacterWithResources,
} from "@/utils/api/types";

export type StoryboardReferenceImageOption = {
  url: string;
  label: string;
};

export type StoryboardCharacterImageOptions = Record<
  number,
  StoryboardReferenceImageOption[]
>;

export function buildCharacterImageOptions(
  character: EpisodeCharacterWithResources,
) {
  const displayName =
    cleanText(character.display_name) ||
    cleanText(character.character_name) ||
    "角色";
  return dedupeReferenceImageOptions(
    (character.resolved_images || []).flatMap((item, index) => {
      const record = asRecord(item);
      const url =
        getString(record?.oss_url) ||
        getString(record?.file_url) ||
        getString(record?.url) ||
        getString(record?.file_path);
      if (!url) return [];
      const category = cleanText(record?.category);
      const subcategory = cleanText(record?.subcategory);
      const suffix = [category, subcategory].filter(Boolean).join(" ");
      return {
        url,
        label: suffix
          ? `${displayName} ${suffix}`
          : `${displayName} ${index + 1}`,
      };
    }),
  );
}

export function buildEnvironmentImageOptions(environment?: Environment | null) {
  return dedupeReferenceImageOptions(
    (environment?.reference_images || []).flatMap((url, index) => {
      const cleaned = cleanText(url);
      if (!cleaned) return [];
      return {
        url: cleaned,
        label: `${environment?.name || "环境"} ${index + 1}`,
      };
    }),
  );
}

export function dedupeReferenceImageOptions(
  options: StoryboardReferenceImageOption[],
) {
  const seen = new Set<string>();
  const deduped: StoryboardReferenceImageOption[] = [];
  for (const option of options) {
    const url = cleanText(option.url);
    if (!url || seen.has(url)) continue;
    seen.add(url);
    deduped.push({ url, label: cleanText(option.label) || url });
  }
  return deduped;
}

export function selectedCharacterReferenceImageUrls(
  optionsByVirtualIp: StoryboardCharacterImageOptions,
  selectedVirtualIpIds: number[],
) {
  return dedupeReferenceImageUrls(
    selectedVirtualIpIds.flatMap((id) =>
      (optionsByVirtualIp[id] || []).map((option) => option.url),
    ),
  );
}

export function toggleReferenceImageUrl(
  previous: string[],
  url: string,
  checked: boolean,
) {
  const cleaned = cleanText(url);
  if (!cleaned) return previous;
  if (checked) return dedupeReferenceImageUrls([...previous, cleaned]);
  return previous.filter((item) => item !== cleaned);
}

export function pruneReferenceImageUrls(previous: string[], allowed: string[]) {
  const allowedSet = new Set(dedupeReferenceImageUrls(allowed));
  return previous.filter((url) => allowedSet.has(url));
}

export function dedupeReferenceImageUrls(values: string[]) {
  const deduped: string[] = [];
  for (const value of values) {
    const cleaned = cleanText(value);
    if (!cleaned || deduped.includes(cleaned)) continue;
    deduped.push(cleaned);
  }
  return deduped;
}

function asRecord(value: unknown) {
  return value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : null;
}

function getString(value: unknown) {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function cleanText(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}
