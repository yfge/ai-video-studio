import { operatorButtonClass, operatorInputClass } from "@/components/shared";
import { outlineLines } from "./storyStructuredOutline";

export function StoryOutlineAction(props: {
  label: string;
  disabled: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={props.disabled}
      onClick={props.onClick}
      className={operatorButtonClass("secondary")}
    >
      {props.label}
    </button>
  );
}

export function StoryOutlineField(props: {
  label: string;
  value: string;
  disabled: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <label className="text-xs font-medium text-gray-600">
      {props.label}
      <textarea
        rows={2}
        value={props.value}
        disabled={props.disabled}
        onChange={(event) => props.onChange(event.target.value)}
        className={operatorInputClass("mt-1 w-full")}
      />
    </label>
  );
}

export function StoryOutlineListField(props: {
  label: string;
  values: string[];
  disabled: boolean;
  onChange: (values: string[]) => void;
}) {
  return (
    <StoryOutlineField
      label={props.label}
      value={props.values.join("\n")}
      disabled={props.disabled}
      onChange={(value) => props.onChange(outlineLines(value))}
    />
  );
}
