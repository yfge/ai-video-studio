import type { StorySeedProgressionArc } from "@/utils/api/types";

export function StoryProgressionArcSelector({
  arcs,
  value,
  onChange,
}: {
  arcs: StorySeedProgressionArc[];
  value: string;
  onChange: (value: string) => void;
}) {
  if (arcs.length <= 1) return null;
  return (
    <label className="flex items-center gap-2 text-xs text-gray-600">
      当前分卷
      <select
        aria-label="当前分卷"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded border border-gray-300 bg-white px-2 py-1"
      >
        {arcs.map((arc) => (
          <option key={arc.arc_id} value={arc.arc_id}>
            {arc.title} · 第 {arc.start_position}–{arc.end_position} 章
          </option>
        ))}
      </select>
    </label>
  );
}
