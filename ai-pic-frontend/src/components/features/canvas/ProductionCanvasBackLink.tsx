import Link from "next/link";
import { operatorButtonClass } from "@/components/shared";

export function ProductionCanvasBackLink() {
  return (
    <div className="hidden sm:block">
      <Link
        href="/stories"
        className={operatorButtonClass("secondary", "whitespace-nowrap")}
      >
        返回故事生产
      </Link>
    </div>
  );
}
