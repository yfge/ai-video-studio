import type { StyleSpec, VirtualIPImage } from "@/utils/api";

type StyleSpecKey = keyof StyleSpec;

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");

export const VIRTUAL_IP_STYLE_SPEC_FIELDS: Array<{ key: StyleSpecKey; label: string }> = [
  { key: "style_universe", label: "世界观 / 画风体系" },
  { key: "character_proportion", label: "人物比例" },
  { key: "character_face_style", label: "五官与人物风格" },
  { key: "line_art_style", label: "线稿风格" },
  { key: "color_render_style", label: "上色方式" },
  { key: "lighting_style", label: "阴影与光影" },
  { key: "color_mood", label: "色彩情绪" },
];

export function resolveImageUrl(image: VirtualIPImage): string {
  if (image.oss_url) return image.oss_url;
  const fp = image.file_path || "";
  if (!fp) return "";
  if (fp.startsWith("http")) return fp;
  return `${API_BASE}${fp.startsWith("/") ? "" : "/"}${fp}`;
}
