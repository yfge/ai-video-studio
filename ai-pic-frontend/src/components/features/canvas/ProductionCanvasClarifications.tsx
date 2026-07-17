import type {
  ProductionCanvasClarification,
  ProductionCanvasProductionContext,
} from "@/utils/api/types";

const inputClass =
  "mt-1.5 h-9 w-full rounded-md border border-amber-200 bg-white px-3 text-sm text-slate-800 focus:border-amber-400 focus:outline-none focus:ring-2 focus:ring-amber-100";

export function ProductionCanvasClarifications({
  answers,
  context,
  onAnswer,
}: {
  answers: Record<string, string>;
  context?: ProductionCanvasProductionContext | null;
  onAnswer: (id: string, value: string) => void;
}) {
  const warnings = context?.brief.interpretation_warnings || [];
  const questions =
    context?.brief.clarifications.filter(
      (item) => item.required && !item.answer,
    ) || [];
  if (!questions.length && !warnings.length) return null;

  return (
    <section
      aria-label="需要补充的生产信息"
      className="mt-3 rounded-lg border border-amber-200 bg-amber-50/70 p-3"
    >
      {warnings.length ? (
        <div>
          <div className="text-sm font-semibold text-amber-900">
            意图解析未完成，已停止自动执行
          </div>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-xs leading-5 text-amber-800">
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {questions.length ? (
        <>
          <div
            className={
              warnings.length
                ? "mt-3 text-sm font-semibold text-amber-900"
                : "text-sm font-semibold text-amber-900"
            }
          >
            生成前还需要你确认 {questions.length} 项
          </div>
          <div className="mt-2 grid gap-3 lg:grid-cols-2">
            {questions.map((question) => (
              <ClarificationField
                key={question.id}
                answer={answers[question.id] || ""}
                question={question}
                onAnswer={(value) => onAnswer(question.id, value)}
              />
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

function ClarificationField({
  answer,
  onAnswer,
  question,
}: {
  answer: string;
  onAnswer: (value: string) => void;
  question: ProductionCanvasClarification;
}) {
  return (
    <label className="min-w-0">
      <span className="block text-[13px] font-medium text-slate-800">
        {question.question}
      </span>
      <span className="mt-0.5 block text-xs leading-5 text-slate-500">
        {question.reason}
      </span>
      {question.options.length ? (
        <select
          aria-label={question.question}
          className={inputClass}
          value={answer}
          onChange={(event) => onAnswer(event.target.value)}
        >
          <option value="">请选择</option>
          {question.options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : (
        <input
          aria-label={question.question}
          className={inputClass}
          value={answer}
          onChange={(event) => onAnswer(event.target.value)}
          placeholder="请输入补充信息"
        />
      )}
    </label>
  );
}
