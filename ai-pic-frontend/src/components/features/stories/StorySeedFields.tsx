import type { Story, StorySeed } from "@/utils/api/types";

export function StorySeedView({ seed }: { seed: StorySeed }) {
  return (
    <div className="grid gap-5 md:grid-cols-2">
      <ReadField label="故事前提" value={seed.premise} />
      <ReadField label="核心冲突" value={seed.central_conflict} />
      <div className="md:col-span-2">
        <ReadField label="整体大纲" value={storySeedOutlineText(seed)} />
      </div>
      <ReadField label="结局方向" value={seed.ending_direction || "未指定"} />
      <ReadField label="目标受众" value={seed.target_audience || "未指定"} />
      <ReadList label="世界规则" values={seed.world_constraints} />
      <ReadList label="内容边界" values={seed.content_constraints} />
      <div className="md:col-span-2">
        <div className="text-xs font-medium text-gray-500">角色初始状态</div>
        <ul className="mt-2 space-y-2 text-sm text-gray-800">
          {seed.protagonists.map((item) => (
            <li
              key={item.virtual_ip_business_id}
              className="rounded-md bg-gray-50 p-3"
            >
              <code className="text-xs">
                {item.virtual_ip_business_id.slice(0, 8)}
              </code>
              <span className="ml-3">{item.initial_state}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export function StorySeedEditor({
  seed,
  onChange,
}: {
  seed: StorySeed;
  onChange: (seed: StorySeed) => void;
}) {
  const field = (key: string, value: unknown) =>
    onChange({ ...seed, [key]: value } as StorySeed);
  const setOutlineText = (value: string) =>
    onChange(
      seed.schema === "story_seed_v2"
        ? { ...seed, outline_text: value }
        : { ...seed, outline: value },
    );
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Editor
        label="故事前提"
        value={seed.premise}
        onChange={(v) => field("premise", v)}
      />
      <Editor
        label="核心冲突"
        value={seed.central_conflict}
        onChange={(v) => field("central_conflict", v)}
      />
      <div className="md:col-span-2">
        <Editor
          label="整体大纲"
          value={storySeedOutlineText(seed)}
          rows={8}
          onChange={setOutlineText}
        />
      </div>
      <Editor
        label="结局方向（可选）"
        value={seed.ending_direction || ""}
        onChange={(v) => field("ending_direction", v || null)}
      />
      <Editor
        label="目标受众"
        value={seed.target_audience || ""}
        onChange={(v) => field("target_audience", v || null)}
      />
      <Editor
        label="世界规则（每行一条）"
        value={seed.world_constraints.join("\n")}
        onChange={(v) => field("world_constraints", lines(v))}
      />
      <Editor
        label="内容边界（每行一条）"
        value={seed.content_constraints.join("\n")}
        onChange={(v) => field("content_constraints", lines(v))}
      />
    </div>
  );
}

function Editor(props: {
  label: string;
  value: string;
  rows?: number;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block text-sm font-medium text-gray-700">
      {props.label}
      <textarea
        value={props.value}
        rows={props.rows || 3}
        onChange={(event) => props.onChange(event.target.value)}
        className="mt-2 w-full rounded-md border border-gray-300 px-3 py-2 focus:ring-2 focus:ring-blue-500"
      />
    </label>
  );
}

function ReadField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs font-medium text-gray-500">{label}</div>
      <p className="mt-1 whitespace-pre-wrap text-sm leading-6 text-gray-800">
        {value}
      </p>
    </div>
  );
}

function ReadList({ label, values }: { label: string; values: string[] }) {
  return (
    <div>
      <div className="text-xs font-medium text-gray-500">{label}</div>
      <ul className="mt-2 list-disc pl-5 text-sm text-gray-800">
        {values.length ? (
          values.map((value) => <li key={value}>{value}</li>)
        ) : (
          <li>未设置</li>
        )}
      </ul>
    </div>
  );
}

function lines(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

export function resolveStorySeed(story: Story): StorySeed {
  if (story.story_seed) return story.story_seed;
  const characters = story.story_characters || story.characters || [];
  return {
    schema: "story_seed_v1",
    title: story.title,
    premise: story.premise || story.title,
    outline: story.synopsis || story.premise || "",
    protagonists: characters.map((item) => ({
      virtual_ip_business_id: item.virtual_ip_business_id || item.business_id,
      initial_state: item.background || item.description || "沿用基础角色设定",
    })),
    world_constraints: story.world_building ? [story.world_building] : [],
    central_conflict: story.main_conflict || "待补充",
    ending_direction: story.resolution || null,
    target_audience: story.target_audience || null,
    content_constraints: [],
  };
}

export function storySeedOutlineText(seed: StorySeed) {
  return seed.schema === "story_seed_v2"
    ? seed.outline_text || seed.outline || ""
    : seed.outline;
}
