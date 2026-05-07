import { redirect } from "next/navigation";
import { episodeWorkspaceHref } from "@/utils/routes";

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
  const tab =
    tabFromQuery === "script" ||
    tabFromQuery === "timeline" ||
    tabFromQuery === "storyboard" ||
    tabFromQuery === "characters" ||
    tabFromQuery === "overview"
      ? tabFromQuery
      : "timeline";

  redirect(
    episodeWorkspaceHref(episodeId, {
      tab,
      scriptId,
      action,
    }),
  );
}
