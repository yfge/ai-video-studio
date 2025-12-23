import { useCallback, useEffect, useMemo, useState } from "react";

import { virtualIPAPI, virtualIPImageAPI, type VirtualIP, type VirtualIPImage } from "@/utils/api";

interface UseVirtualIPImageDataOptions {
  virtualIPKey: string;
  showAlert: (opts: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
  }) => void;
}

export function useVirtualIPImageData({ virtualIPKey, showAlert }: UseVirtualIPImageDataOptions) {
  const [virtualIP, setVirtualIP] = useState<VirtualIP | null>(null);
  const [virtualIPId, setVirtualIPId] = useState<number | null>(null);
  const [images, setImages] = useState<VirtualIPImage[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const ipResponse = await virtualIPAPI.getVirtualIP(virtualIPKey);

      if (ipResponse.success && ipResponse.data) {
        setVirtualIP(ipResponse.data);
        setVirtualIPId(ipResponse.data.id);

        const [imagesResponse, categoriesResponse] = await Promise.all([
          virtualIPImageAPI.getImages(ipResponse.data.id),
          virtualIPImageAPI.getCategories(ipResponse.data.id),
        ]);

        setImages(imagesResponse.success && imagesResponse.data ? imagesResponse.data : []);
        setCategories(
          categoriesResponse.success && categoriesResponse.data ? categoriesResponse.data : [],
        );
      } else {
        showAlert({ message: "加载虚拟IP失败", variant: "error" });
        setImages([]);
        setCategories([]);
      }
    } catch (error) {
      console.error("Failed to load data:", error);
      showAlert({ message: "加载数据失败", variant: "error" });
      setImages([]);
      setCategories([]);
    } finally {
      setLoading(false);
    }
  }, [showAlert, virtualIPKey]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const filteredImages = useMemo(
    () => (selectedCategory ? images.filter((img) => img.category === selectedCategory) : images),
    [images, selectedCategory],
  );

  return {
    virtualIP,
    virtualIPId,
    images,
    setImages,
    categories,
    selectedCategory,
    setSelectedCategory,
    loading,
    filteredImages,
  };
}
