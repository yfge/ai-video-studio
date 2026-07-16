export function productionCanvasReferenceArtifactMatchesContext(
  value: string,
  virtualIpId?: number,
  environmentId?: number,
) {
  if (value.startsWith("virtual_ip_image:")) {
    return Boolean(
      virtualIpId && value.startsWith(`virtual_ip_image:${virtualIpId}:`),
    );
  }
  if (value.startsWith("environment_images:")) {
    return Boolean(
      environmentId && value.startsWith(`environment_images:${environmentId}:`),
    );
  }
  return true;
}
