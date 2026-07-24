import { operatorInputClass } from "@/components/shared";
import type { NovelLengthRange } from "@/utils/api/types";

export function StoryNovelLengthRangeFields(props: {
  value: NovelLengthRange;
  disabled: boolean;
  onChange: (value: NovelLengthRange) => void;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-3">
      {(["min_chars", "target_chars", "max_chars"] as const).map((key) => (
        <label key={key} className="text-xs font-medium text-gray-600">
          {rangeLabels[key]}
          <input
            type="number"
            min={1}
            step={1}
            disabled={props.disabled}
            value={props.value[key]}
            onChange={(event) =>
              props.onChange({
                ...props.value,
                [key]: Number(event.target.value),
              })
            }
            className={operatorInputClass("mt-1 w-full")}
          />
        </label>
      ))}
    </div>
  );
}

const rangeLabels: Record<keyof NovelLengthRange, string> = {
  min_chars: "最小字数",
  target_chars: "目标字数",
  max_chars: "最大字数",
};
