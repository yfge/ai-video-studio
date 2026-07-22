import { operatorButtonClass, operatorInputClass } from "@/components/shared";
import type { AdaptationPlanEpisode } from "@/utils/api/types";

interface Props {
  row: AdaptationPlanEpisode;
  index: number;
  busy: boolean;
  editable: boolean;
  canRemove: boolean;
  onChange: (patch: Partial<AdaptationPlanEpisode>) => void;
  onRemove: () => void;
}

const lines = (value: string) =>
  value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);

export const parseCharacterArcs = (value: string) =>
  Object.fromEntries(
    lines(value).map((item) => {
      const separator = item.indexOf(":");
      if (separator < 0) return [item, ""];
      return [
        item.slice(0, separator).trim(),
        item.slice(separator + 1).trim(),
      ];
    }),
  );

const characterArcText = (row: AdaptationPlanEpisode) =>
  Object.entries(row.character_arcs)
    .map(([character, arc]) => `${character}: ${String(arc ?? "")}`)
    .join("\n");

export function StoryNovelAdaptationEpisodeCard({
  row,
  index,
  busy,
  editable,
  canRemove,
  onChange,
  onRemove,
}: Props) {
  const label = `第${index + 1}集`;
  return (
    <article className="rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-3">
        <strong className="text-sm">第 {index + 1} 集</strong>
        <button
          type="button"
          disabled={busy || !editable || !canRemove}
          onClick={onRemove}
          className={operatorButtonClass("secondary")}
        >
          删除
        </button>
      </div>
      <fieldset disabled={!editable}>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <input
            aria-label={`${label}标题`}
            value={row.title}
            onChange={(event) =>
              onChange({
                title: event.target.value,
                episode_number: index + 1,
              })
            }
            className={operatorInputClass("w-full")}
            placeholder="集标题"
          />
          <input
            aria-label={`${label}来源章节`}
            value={row.source_chapter_business_ids.join(",")}
            onChange={(event) =>
              onChange({
                source_chapter_business_ids: event.target.value
                  .split(",")
                  .map((item) => item.trim())
                  .filter(Boolean),
              })
            }
            className={operatorInputClass("w-full")}
            placeholder="章节 business ID，逗号分隔"
          />
        </div>
        <textarea
          aria-label={`${label}改编目标`}
          value={row.adaptation_goal}
          onChange={(event) =>
            onChange({ adaptation_goal: event.target.value })
          }
          className={operatorInputClass("mt-3 min-h-16 w-full")}
          placeholder="改编目标"
        />
        <textarea
          aria-label={`${label}概要`}
          value={row.summary}
          onChange={(event) => onChange({ summary: event.target.value })}
          className={operatorInputClass("mt-3 min-h-24 w-full")}
          placeholder="本集概要"
        />
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <textarea
            aria-label={`${label}情节点`}
            value={row.plot_points.join("\n")}
            onChange={(event) =>
              onChange({ plot_points: lines(event.target.value) })
            }
            className={operatorInputClass("min-h-24 w-full")}
            placeholder="情节点，每行一个"
          />
          <textarea
            aria-label={`${label}冲突`}
            value={row.conflicts.join("\n")}
            onChange={(event) =>
              onChange({ conflicts: lines(event.target.value) })
            }
            className={operatorInputClass("min-h-24 w-full")}
            placeholder="冲突，每行一个"
          />
        </div>
        <textarea
          aria-label={`${label}角色弧`}
          value={characterArcText(row)}
          onInput={(event) =>
            onChange({
              character_arcs: parseCharacterArcs(event.currentTarget.value),
            })
          }
          className={operatorInputClass("mt-3 min-h-20 w-full")}
          placeholder="角色: 本集角色弧，每行一个"
        />
        <input
          aria-label={`${label}卡点`}
          value={row.cliffhanger || ""}
          onChange={(event) => onChange({ cliffhanger: event.target.value })}
          className={operatorInputClass("mt-3 w-full")}
          placeholder="章末卡点"
        />
      </fieldset>
    </article>
  );
}
