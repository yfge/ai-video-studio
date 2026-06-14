export function operatorShellHeaderClass(compactNavigation: boolean) {
  const heightClass = compactNavigation ? "h-8 min-[760px]:h-10" : "h-14";
  const paddingClass = compactNavigation ? "px-3 sm:px-4" : "px-4 sm:px-5";
  const alignmentClass = compactNavigation
    ? "justify-end min-[760px]:justify-between"
    : "justify-between";
  return [
    "sticky top-0 z-30 flex items-center border-b border-gray-200 bg-white/95 backdrop-blur",
    alignmentClass,
    heightClass,
    paddingClass,
  ].join(" ");
}

export function operatorShellMainClass(compactNavigation: boolean) {
  return compactNavigation ? "px-4 py-2 sm:px-5 sm:py-3" : "px-4 py-4 sm:px-5";
}

export function operatorShellSidebarHeaderClass(compactNavigation: boolean) {
  const heightClass = compactNavigation ? "h-10" : "h-14";
  const layoutClass = compactNavigation ? "justify-center px-2" : "px-4";
  return [
    "flex items-center border-b border-gray-200",
    heightClass,
    layoutClass,
  ].join(" ");
}

export function operatorShellTitleClass(compactNavigation: boolean) {
  return compactNavigation ? "min-w-0 max-[760px]:sr-only" : "min-w-0";
}

export function operatorShellActionsClass(compactNavigation: boolean) {
  return compactNavigation
    ? "flex items-center gap-1.5 min-[760px]:gap-2"
    : "flex items-center gap-3";
}

export function operatorShellUserClass(compactNavigation: boolean) {
  return compactNavigation
    ? "inline-flex h-6 max-w-24 items-center truncate rounded-md border border-gray-200 bg-white px-1.5 text-[11px] text-gray-600 min-[760px]:h-7 min-[760px]:px-2"
    : "rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-600";
}

export function operatorShellLogoutButtonClass(compactNavigation: boolean) {
  return compactNavigation
    ? "!h-6 !px-1.5 text-[11px] min-[760px]:!h-7 min-[760px]:!px-2"
    : "";
}
