import { redirect } from "next/navigation";

type EpisodePageProps = {
  params: Promise<{ id: string }>;
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function EpisodePage({
  params,
  searchParams,
}: EpisodePageProps) {
  const { id: episodeId } = await params;
  const resolvedSearchParams = (await searchParams) ?? {};
  const action =
    typeof resolvedSearchParams.action === "string"
      ? resolvedSearchParams.action
      : undefined;
  const tabFromQuery =
    typeof resolvedSearchParams.tab === "string"
      ? resolvedSearchParams.tab
      : undefined;
  const scriptId =
    typeof resolvedSearchParams.scriptId === "string"
      ? resolvedSearchParams.scriptId
      : undefined;

  const outParams = new URLSearchParams();
  outParams.set(
    "tab",
    tabFromQuery || (action === "generate-timeline" ? "timeline" : "overview"),
  );
  if (scriptId) outParams.set("scriptId", scriptId);
  if (action) outParams.set("action", action);

  redirect(`/episodes/${episodeId}/workspace?${outParams.toString()}`);
}
