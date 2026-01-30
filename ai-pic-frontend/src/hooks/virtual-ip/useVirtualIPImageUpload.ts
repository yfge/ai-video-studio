import { useState } from "react";

import { virtualIPImageAPI, type VirtualIPImage } from "@/utils/api";

import type { UploadFormState } from "./virtualIpImageTypes";

interface UseVirtualIPImageUploadOptions {
  virtualIPId: number | null;
  setImages: React.Dispatch<React.SetStateAction<VirtualIPImage[]>>;
  showAlert: (opts: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
  }) => void;
}

export function useVirtualIPImageUpload({
  virtualIPId,
  setImages,
  showAlert,
}: UseVirtualIPImageUploadOptions) {
  const [uploadForm, setUploadForm] = useState<UploadFormState>({
    file: null,
    category: "portrait",
    tags: "",
    is_default: false,
  });
  const [uploading, setUploading] = useState(false);

  const handleUploadImage = async () => {
    if (!uploadForm.file) {
      showAlert({ message: "请选择文件", variant: "warning" });
      return;
    }
    if (!virtualIPId) {
      showAlert({ message: "虚拟IP尚未加载", variant: "error" });
      return;
    }

    try {
      setUploading(true);
      const response = await virtualIPImageAPI.uploadImage(
        virtualIPId,
        uploadForm.file,
        uploadForm.category,
        uploadForm.tags,
        uploadForm.is_default,
      );

      if (response.success && response.data) {
        setImages((prev) => [response.data as VirtualIPImage, ...prev]);
        setUploadForm({
          file: null,
          category: "portrait",
          tags: "",
          is_default: false,
        });
        showAlert({ message: "图片上传成功！", variant: "success" });
      } else {
        throw new Error(response.error || "图片上传失败");
      }
    } catch (error) {
      console.error("Image upload failed:", error);
      showAlert({
        message: `图片上传失败：${
          error instanceof Error ? error.message : "未知错误"
        }`,
        variant: "error",
      });
    } finally {
      setUploading(false);
    }
  };

  return {
    uploadForm,
    setUploadForm,
    uploading,
    handleUploadImage,
  };
}
