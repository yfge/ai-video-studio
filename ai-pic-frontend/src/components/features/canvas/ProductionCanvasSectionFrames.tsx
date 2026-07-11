import type { ProductionCanvasSection } from "./productionCanvasSectionModel";

export function ProductionCanvasSectionFrames({
  sections,
  worldBounds,
  onToggle,
}: {
  sections: ProductionCanvasSection[];
  worldBounds: { minX: number; minY: number };
  onToggle: (sectionId: string) => void;
}) {
  return sections.map((section) => (
    <section
      key={section.id}
      aria-label={section.title}
      className={`absolute z-0 border-2 border-dashed ${
        section.scope === "scene"
          ? "border-cyan-300 bg-cyan-50/30"
          : "border-amber-300 bg-amber-50/30"
      }`}
      data-canvas-section={section.id}
      style={{
        left: section.x - worldBounds.minX,
        top: section.y - worldBounds.minY,
        width: section.width,
        height: section.collapsed ? 40 : section.height,
      }}
    >
      <button
        type="button"
        aria-expanded={!section.collapsed}
        className="flex h-9 w-full items-center justify-between px-3 text-left text-xs font-semibold text-gray-800"
        onPointerDown={(event) => event.stopPropagation()}
        onClick={() => onToggle(section.id)}
      >
        <span>{section.title}</span>
        <span aria-hidden="true">{section.collapsed ? "+" : "−"}</span>
      </button>
    </section>
  ));
}
