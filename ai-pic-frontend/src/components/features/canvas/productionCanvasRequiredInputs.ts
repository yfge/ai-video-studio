function outputNumber(outputs: Record<string, unknown>, key: string) {
  const value = outputs[key];
  return typeof value === "number" && Number.isFinite(value)
    ? value
    : undefined;
}

function firstOutputNumber(outputs: Record<string, unknown>, key: string) {
  const value = outputs[key];
  if (!Array.isArray(value)) return undefined;
  const first = value.find((item) => typeof item === "number");
  return typeof first === "number" ? first : undefined;
}

function outputString(outputs: Record<string, unknown>, key: string) {
  const value = outputs[key];
  return typeof value === "string" && value.trim() ? value : undefined;
}

function requiredInputSatisfied(
  input: unknown,
  outputs: Record<string, unknown>,
) {
  if (input === "virtual_ip_id") {
    return firstOutputNumber(outputs, "virtual_ip_ids");
  }
  if (input === "environment_id") {
    return firstOutputNumber(outputs, "environment_ids");
  }
  if (input === "reference_artifacts") {
    return (
      Array.isArray(outputs.reference_artifacts) &&
      outputs.reference_artifacts.length > 0
    );
  }
  if (input === "clip_id") return outputString(outputs, "clip_id");
  if (typeof input === "string") return outputNumber(outputs, input);
  return false;
}

export function missingProductionCanvasRequiredInputs(
  rawRequiredInputs: unknown,
  outputs: Record<string, unknown>,
) {
  if (!Array.isArray(rawRequiredInputs)) return [];
  return rawRequiredInputs.filter(
    (input) => !requiredInputSatisfied(input, outputs),
  );
}
