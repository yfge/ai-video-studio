import type { LabeledReferenceImage, ReferenceSection } from "./types";

export function buildLabeledReferences(
  refs: string[],
  referenceSections: ReferenceSection[],
): LabeledReferenceImage[] {
  return refs.reduce<LabeledReferenceImage[]>((acc, url) => {
    const section = referenceSections.find((s) => s.images.includes(url));
    if (!section) return acc;
    acc.push({
      url,
      type: section.imageType || "other",
      label: section.imageLabel,
    });
    return acc;
  }, []);
}
