export type RequestPayload = Record<string, unknown>;
export type FetchInput = Parameters<typeof fetch>[0];
export type FetchInit = Parameters<typeof fetch>[1];

export type PlannerFetchStub = {
  executeRequests: RequestPayload[];
  planRequests: RequestPayload[];
  restore: () => void;
  taskRequests: string[];
};

const headers = { "content-type": "application/json" };

export function jsonResponse(data: unknown): Promise<Response> {
  return Promise.resolve(
    new Response(JSON.stringify({ success: true, data }), { headers }),
  );
}

export function parseRequestBody(init: FetchInit): RequestPayload {
  return JSON.parse(String(init?.body ?? "{}")) as RequestPayload;
}

export function taskData({
  errorMessage,
  id,
  progress,
  resultContext,
  status,
  taskType,
  title,
  updatedAt,
}: {
  errorMessage?: string;
  id: number;
  progress: string;
  resultContext?: Record<string, unknown>;
  status: string;
  taskType: string;
  title: string;
  updatedAt: string;
}) {
  return {
    id,
    business_id: `task-${id}`,
    title,
    task_type: taskType,
    status,
    progress_detail: progress,
    ...(errorMessage ? { error_message: errorMessage } : {}),
    created_at: "2026-07-02T00:00:00Z",
    updated_at: updatedAt,
    user_id: 1,
    parameters: {},
    ...(resultContext ? { result_context: resultContext } : {}),
  };
}

export function skillNode(fields: RequestPayload) {
  return {
    width: 220,
    kind: "skill_result",
    reuse_targets: [],
    ...fields,
  };
}

export function reuseTarget(kind: string, label: string, target: string) {
  return { kind, label, target };
}
