export function ProgressBar({
  value,
  tone = "blue",
}: {
  value: number;
  tone?: "blue" | "green" | "amber" | "red";
}) {
  const clamped = Math.min(100, Math.max(0, value));
  const fillClass = {
    blue: "bg-blue-600",
    green: "bg-green-600",
    amber: "bg-amber-500",
    red: "bg-red-500",
  }[tone];
  return (
    <div className="h-1.5 w-full overflow-hidden rounded bg-gray-100">
      <div
        className={`h-full rounded ${fillClass}`}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
