import type { EpisodeCharacter } from "@/utils/api/types";
import { episodeCharacterDisplayName } from "./episodeCharacterDisplay";
import type { ReferenceImagePickerGroup } from "./TimelineClipReferenceImagePickerModal";
import type {
  StoryboardCharacterImageOptions,
  StoryboardReferenceImageOption,
} from "./TimelineClipStoryboardReferenceImagesModel";

export function buildCharacterImageGroups(
  selectedVirtualIpIds: number[],
  characterImageOptions: StoryboardCharacterImageOptions,
  episodeCharacters: EpisodeCharacter[],
): ReferenceImagePickerGroup[] {
  return selectedVirtualIpIds
    .map((virtualIpId) => {
      const options = characterImageOptions[virtualIpId] || [];
      return {
        key: String(virtualIpId),
        title: characterLabelForVirtualIp(episodeCharacters, virtualIpId),
        sections: groupReferenceOptionsByCategory(options),
      };
    })
    .filter((group) =>
      group.sections.some((section) => section.options.length),
    );
}

export function buildEnvironmentImageGroups(
  environmentImageOptions: StoryboardReferenceImageOption[],
): ReferenceImagePickerGroup[] {
  const sections = groupReferenceOptionsByCategory(environmentImageOptions);
  return sections.some((section) => section.options.length)
    ? [{ key: "environment", title: "当前环境", sections }]
    : [];
}

function groupReferenceOptionsByCategory(
  options: StoryboardReferenceImageOption[],
) {
  const grouped = new Map<string, StoryboardReferenceImageOption[]>();
  for (const option of options) {
    const category = categoryFromLabel(option.label);
    grouped.set(category, [...(grouped.get(category) || []), option]);
  }
  return Array.from(grouped.entries()).map(([title, items]) => ({
    key: title,
    title,
    options: items,
  }));
}

function categoryFromLabel(label: string) {
  const normalized = label.toLocaleLowerCase();
  if (/full[_\s-]?body|全身/.test(normalized)) return "full_body";
  if (/half[_\s-]?body|半身/.test(normalized)) return "half_body";
  if (/portrait|头像|正面/.test(normalized)) return "portrait";
  return "其他";
}

function characterLabelForVirtualIp(
  characters: EpisodeCharacter[],
  virtualIpId: number,
) {
  const character = characters.find((item) => item.virtual_ip_id === virtualIpId);
  return character
    ? episodeCharacterDisplayName(character, `IP ${virtualIpId}`)
    : `IP ${virtualIpId}`;
}
