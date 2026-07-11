import { productionCanvasAPI } from "@/utils/api/endpoints";

type CandidateResponse = Awaited<
  ReturnType<typeof productionCanvasAPI.getNodeCandidates>
>;

export async function loadProductionCanvasCandidates(
  runId: string,
  nodeId: string,
  request = productionCanvasAPI.getNodeCandidates,
  wait: (milliseconds: number) => Promise<void> = (milliseconds) =>
    new Promise((resolve) => setTimeout(resolve, milliseconds)),
): Promise<CandidateResponse> {
  const response = await request(runId, nodeId);
  if (response.success || !response.error?.includes("404")) return response;
  await wait(1500);
  return request(runId, nodeId);
}
