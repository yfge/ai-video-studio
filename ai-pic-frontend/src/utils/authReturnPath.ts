const DEFAULT_RETURN_PATH = "/";

export function resolveSafeLoginReturnPath(raw: string | null | undefined) {
  const value = raw?.trim();
  if (!value) return DEFAULT_RETURN_PATH;
  if (!value.startsWith("/") || value.startsWith("//")) {
    return DEFAULT_RETURN_PATH;
  }
  if (value === "/login" || value.startsWith("/login?")) {
    return DEFAULT_RETURN_PATH;
  }
  return value;
}

export function buildLoginPathForReturn(raw: string | null | undefined) {
  const safePath = resolveSafeLoginReturnPath(raw);
  if (safePath === DEFAULT_RETURN_PATH) return "/login";
  return `/login?next=${encodeURIComponent(safePath)}`;
}

export function currentBrowserReturnPath() {
  if (typeof window === "undefined") return DEFAULT_RETURN_PATH;
  return `${window.location.pathname}${window.location.search}${window.location.hash}`;
}
