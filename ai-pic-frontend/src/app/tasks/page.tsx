import { TasksPage } from "@/components/features/tasks/TasksPage";

function parseTaskId(value: string | string[] | undefined) {
  const raw = Array.isArray(value) ? value[0] : value;
  if (!raw) return null;
  const taskId = Number(raw);
  return Number.isInteger(taskId) && taskId > 0 ? taskId : null;
}

export default async function Tasks({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const resolvedSearchParams = (await searchParams) ?? {};
  return <TasksPage targetTaskId={parseTaskId(resolvedSearchParams.task_id)} />;
}
