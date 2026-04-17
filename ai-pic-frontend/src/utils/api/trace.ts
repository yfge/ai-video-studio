export interface ApiTraceMeta {
  clientRequestId?: string;
  harnessRunId?: string;
  requestId?: string;
}

function randomId() {
  return Math.random().toString(36).slice(2, 10);
}

export function getHarnessRunId(): string | undefined {
  if (typeof window !== "undefined") {
    const fromStorage = window.sessionStorage.getItem("harness_run_id");
    if (fromStorage) {
      return fromStorage;
    }
  }
  return process.env.NEXT_PUBLIC_HARNESS_RUN_ID || undefined;
}

export function createClientRequestId(): string {
  return `req-${Date.now()}-${randomId()}`;
}

export function buildTraceHeaders(): ApiTraceMeta {
  const harnessRunId = getHarnessRunId();
  return {
    clientRequestId: createClientRequestId(),
    harnessRunId,
  };
}

export function applyTraceHeaders(headers: Record<string, string>): ApiTraceMeta {
  const trace = buildTraceHeaders();
  if (trace.clientRequestId) {
    headers["X-Client-Request-ID"] = trace.clientRequestId;
  }
  if (trace.harnessRunId) {
    headers["X-Harness-Run-ID"] = trace.harnessRunId;
  }
  return trace;
}

export function readTraceHeaders(response: Response, trace: ApiTraceMeta): ApiTraceMeta {
  return {
    ...trace,
    requestId: response.headers.get("x-request-id") || undefined,
    harnessRunId:
      response.headers.get("x-harness-run-id") || trace.harnessRunId,
  };
}
