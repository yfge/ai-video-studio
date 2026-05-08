import type { Environment, VirtualIPEnvironmentLink } from "@/utils/api/types";

export function uniqueEnvironmentLinks(links: VirtualIPEnvironmentLink[]) {
  const unique = new Map<number, VirtualIPEnvironmentLink>();
  links.forEach((link) => unique.set(link.environment_id, link));
  return Array.from(unique.values());
}

export function availableEnvironmentOptions(
  environments: Environment[],
  links: VirtualIPEnvironmentLink[],
) {
  const linkedIds = new Set(links.map((link) => link.environment_id));
  return environments.filter((env) => !linkedIds.has(env.id));
}
