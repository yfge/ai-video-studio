import { virtualIPImageAPI } from "@/utils/api/endpoints";
import type { VirtualIPImage } from "@/utils/api/types";

interface UseVirtualIPImageActionsOptions {
  virtualIPId: number | null;
  setImages: React.Dispatch<React.SetStateAction<VirtualIPImage[]>>;
  showAlert: (opts: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
    title?: string;
    confirmText?: string;
    onConfirm?: () => void;
  }) => void;
}

export function useVirtualIPImageActions({
  virtualIPId,
  setImages,
  showAlert,
}: UseVirtualIPImageActionsOptions) {
  const handleDeleteImage = (imageId: number) => {
    showAlert({
      title: "确认删除图片",
      message: "确定删除这张图片吗？",
      variant: "warning",
      confirmText: "删除",
      onConfirm: async () => {
        if (!virtualIPId) {
          showAlert({ message: "虚拟IP尚未加载", variant: "error" });
          return;
        }
        try {
          const response = await virtualIPImageAPI.deleteImage(
            virtualIPId,
            imageId,
          );
          if (response.success) {
            setImages((prev) => prev.filter((img) => img.id !== imageId));
            showAlert({ message: "图片删除成功", variant: "success" });
          } else {
            throw new Error(response.error || "删除图片失败");
          }
        } catch (error) {
          console.error("Delete image failed:", error);
          showAlert({
            message: `删除图片失败：${
              error instanceof Error ? error.message : "未知错误"
            }`,
            variant: "error",
          });
        }
      },
    });
  };

  const handleSetDefault = async (imageId: number) => {
    if (!virtualIPId) {
      showAlert({ message: "虚拟IP尚未加载", variant: "error" });
      return;
    }
    try {
      const response = await virtualIPImageAPI.setDefaultImage(
        virtualIPId,
        imageId,
      );
      if (response.success) {
        setImages((prev) =>
          prev.map((img) => ({ ...img, is_default: img.id === imageId })),
        );
        showAlert({ message: "已设置为默认图片", variant: "success" });
      } else {
        throw new Error(response.error || "设置默认图片失败");
      }
    } catch (error) {
      console.error("Set default image failed:", error);
      showAlert({
        message: `设置默认图片失败：${
          error instanceof Error ? error.message : "未知错误"
        }`,
        variant: "error",
      });
    }
  };

  return { handleDeleteImage, handleSetDefault };
}
