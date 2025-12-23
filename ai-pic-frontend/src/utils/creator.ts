import type { CreatorInfo } from "@/utils/api";

export const resolveCreatorLabel = (creator?: CreatorInfo | null) => {
  if (!creator) return "未知";
  const fullName = creator.full_name?.trim();
  if (fullName) return fullName;
  if (creator.username) return creator.username;
  return `用户${creator.id}`;
};
