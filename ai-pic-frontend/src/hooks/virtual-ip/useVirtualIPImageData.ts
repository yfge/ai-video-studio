import { useCallback, useEffect, useMemo, useState } from "react";

import { virtualIPAPI, virtualIPImageAPI, type VirtualIP, type VirtualIPImage } from "@/utils/api";

interface UseVirtualIPImageDataOptions {
  virtualIPKey: string;
  virtualIP?: VirtualIP | null;
  skipVirtualIPFetch?: boolean;
  showAlert: (opts: {
    message: string;
    variant: "success" | "error" | "warning" | "info";
  }) => void;
}

export function useVirtualIPImageData({
  virtualIPKey,
  virtualIP: initialVirtualIP,
  skipVirtualIPFetch = false,
  showAlert,
}: UseVirtualIPImageDataOptions) {
  const [virtualIP, setVirtualIP] = useState<VirtualIP | null>(initialVirtualIP ?? null);
  const [virtualIPId, setVirtualIPId] = useState<number | null>(initialVirtualIP?.id ?? null);
  const [images, setImages] = useState<VirtualIPImage[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!initialVirtualIP) return;
    setVirtualIP(initialVirtualIP);
    setVirtualIPId(initialVirtualIP.id);
  }, [initialVirtualIP]);

  const loadData = useCallback(async () => {
    if (skipVirtualIPFetch && !initialVirtualIP) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      let ip = initialVirtualIP;
      if (!ip) {
        const ipResponse = await virtualIPAPI.getVirtualIP(virtualIPKey);
        if (ipResponse.success && ipResponse.data) {
          ip = ipResponse.data;
        } else {
          showAlert({ message: "加载虚拟IP失败", variant: "error" });
          setImages([]);
          setCategories([]);
          return;
        }
      }

      setVirtualIP(ip);
      setVirtualIPId(ip.id);

      const [imagesResponse, categoriesResponse] = await Promise.all([
        virtualIPImageAPI.getImages(ip.id),
        virtualIPImageAPI.getCategories(ip.id),
      ]);

      setImages(imagesResponse.success && imagesResponse.data ? imagesResponse.data : []);
      setCategories(
        categoriesResponse.success && categoriesResponse.data ? categoriesResponse.data : [],
      );
    } catch (error) {
      console.error("Failed to load data:", error);
      showAlert({ message: "加载数据失败", variant: "error" });
      setImages([]);
      setCategories([]);
    } finally {
      setLoading(false);
    }
  }, [initialVirtualIP, showAlert, skipVirtualIPFetch, virtualIPKey]);

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
