const CATEGORY_LABELS: Record<string, string> = {
  portrait: "肖像",
  full_body: "全身",
  scene: "场景",
  action: "动作",
  emotion: "情绪",
};

export const getCategoryLabel = (category: string): string =>
  CATEGORY_LABELS[category] || category;
