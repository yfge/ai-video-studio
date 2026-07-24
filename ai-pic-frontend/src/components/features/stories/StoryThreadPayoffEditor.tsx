"use client";

import {
  operatorButtonClass,
  operatorInputClass,
  operatorTableClass,
} from "@/components/shared";
import type {
  StorySeedStructuredChapter,
  StorySeedThreadPayoff,
} from "@/utils/api/types";

interface Props {
  chapters: StorySeedStructuredChapter[];
  payoffs: StorySeedThreadPayoff[];
  disabled: boolean;
  onChange: (payoffs: StorySeedThreadPayoff[]) => void;
}

export function StoryThreadPayoffEditor({
  chapters,
  payoffs,
  disabled,
  onChange,
}: Props) {
  const threads = chapters.flatMap((chapter) =>
    chapter.open_threads.map((threadId) => ({
      threadId,
      openingPosition: chapter.position,
    })),
  );
  const patch = (index: number, value: Partial<StorySeedThreadPayoff>) =>
    onChange(
      payoffs.map((payoff, row) =>
        row === index ? { ...payoff, ...value } : payoff,
      ),
    );
  const add = () => {
    const used = new Set(payoffs.map((item) => item.thread_id));
    const opening = threads.find((item) => !used.has(item.threadId));
    if (!opening) return;
    const target =
      chapters.find((item) => item.position > opening.openingPosition) ??
      chapters.at(-1);
    onChange([
      ...payoffs,
      {
        thread_id: opening.threadId,
        payoff_position: target?.position ?? opening.openingPosition,
        evidence_key_event: target?.key_events[0] ?? "",
      },
    ]);
  };

  return (
    <section className="space-y-2" aria-label="伏笔回收合同">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">伏笔回收表</h3>
        <button
          type="button"
          disabled={disabled || payoffs.length >= threads.length}
          onClick={add}
          className={operatorButtonClass("secondary")}
        >
          增加回收
        </button>
      </div>
      {threads.length ? (
        <div className="overflow-x-auto">
          <table className={`${operatorTableClass} min-w-[760px]`}>
            <thead>
              <tr>
                <th>伏笔 ID</th>
                <th>回收章节</th>
                <th>关键事件证据</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {payoffs.map((payoff, index) => {
                const target = chapters.find(
                  (chapter) => chapter.position === payoff.payoff_position,
                );
                return (
                  <tr key={`${payoff.thread_id}-${index}`}>
                    <td>
                      <select
                        aria-label={`第 ${index + 1} 条伏笔 ID`}
                        value={payoff.thread_id}
                        disabled={disabled}
                        onChange={(event) =>
                          patch(index, { thread_id: event.target.value })
                        }
                        className={operatorInputClass("w-full")}
                      >
                        {!threads.some(
                          (item) => item.threadId === payoff.thread_id,
                        ) ? (
                          <option value={payoff.thread_id}>
                            {payoff.thread_id || "未知伏笔"}
                          </option>
                        ) : null}
                        {threads.map((item) => (
                          <option
                            key={`${item.openingPosition}-${item.threadId}`}
                            value={item.threadId}
                          >
                            {item.threadId}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <select
                        aria-label={`第 ${index + 1} 条回收章节`}
                        value={payoff.payoff_position}
                        disabled={disabled}
                        onChange={(event) => {
                          const position = Number(event.target.value);
                          const chapter = chapters.find(
                            (item) => item.position === position,
                          );
                          patch(index, {
                            payoff_position: position,
                            evidence_key_event: chapter?.key_events[0] ?? "",
                          });
                        }}
                        className={operatorInputClass("w-full")}
                      >
                        {chapters.map((chapter) => (
                          <option
                            key={chapter.position}
                            value={chapter.position}
                          >
                            第 {chapter.position} 章
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <select
                        aria-label={`第 ${index + 1} 条关键事件证据`}
                        value={payoff.evidence_key_event}
                        disabled={disabled}
                        onChange={(event) =>
                          patch(index, {
                            evidence_key_event: event.target.value,
                          })
                        }
                        className={operatorInputClass("w-full")}
                      >
                        {!target?.key_events.includes(
                          payoff.evidence_key_event,
                        ) ? (
                          <option value={payoff.evidence_key_event}>
                            {payoff.evidence_key_event || "选择关键事件"}
                          </option>
                        ) : null}
                        {(target?.key_events ?? []).map((event, eventIndex) => (
                          <option key={`${eventIndex}-${event}`} value={event}>
                            {event}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <button
                        type="button"
                        disabled={disabled}
                        onClick={() =>
                          onChange(payoffs.filter((_, row) => row !== index))
                        }
                        className={operatorButtonClass("secondary")}
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-xs text-gray-500">当前大纲没有伏笔，回收表为空。</p>
      )}
    </section>
  );
}
