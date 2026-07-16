export function waitForProductionCanvasBusyPaint() {
  if (
    typeof window !== "undefined" &&
    typeof window.requestAnimationFrame === "function"
  ) {
    return new Promise<void>((resolve) => {
      window.requestAnimationFrame(() => resolve());
    });
  }
  return new Promise<void>((resolve) => {
    setTimeout(resolve, 0);
  });
}

export function afterProductionCanvasPaint(callback: () => void) {
  void waitForProductionCanvasBusyPaint().then(callback);
}
