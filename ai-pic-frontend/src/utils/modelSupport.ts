import type { AIModel } from "@/utils/api";

type ModelUiMetadata = {
  supports_reference_image?: boolean;
  supportsReferenceImage?: boolean;
};

type ModelMetadata = {
  ui?: ModelUiMetadata;
};

export function supportsReferenceImage(model?: AIModel): boolean {
  if (!model) return false;

  const ui = (model.metadata as ModelMetadata | undefined)?.ui;
  const flag = ui?.supports_reference_image ?? ui?.supportsReferenceImage;
  if (typeof flag === "boolean") return flag;

  if (model.capabilities?.includes("image_to_image")) return true;
  return model.type === "image_to_image";
}
