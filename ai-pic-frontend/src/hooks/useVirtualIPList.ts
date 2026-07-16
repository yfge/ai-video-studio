"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { virtualIPAPI } from "@/utils/api/endpoints";
import type { VirtualIP } from "@/utils/api/types";
import type { AlertOptions } from "@/components/shared/modals/AlertModalProvider";
import { fetchAllPages } from "@/utils/api/pagination";
import { resolveCreatorLabel } from "@/utils/creator";

interface UseVirtualIPListOptions {
  showAlert: (options: AlertOptions) => void;
}

export function useVirtualIPList({ showAlert }: UseVirtualIPListOptions) {
  const [allVirtualIPs, setAllVirtualIPs] = useState<VirtualIP[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const fetchVirtualIPs = useCallback(async () => {
    try {
      setLoading(true);
      const items = await fetchAllPages((skip, limit) =>
        virtualIPAPI.getVirtualIPs({ skip, limit }),
      );
      setAllVirtualIPs(items);
    } catch (error) {
      console.error("获取虚拟IP列表出错:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchVirtualIPs();
  }, [fetchVirtualIPs]);

  const virtualIPs = useMemo(() => {
    const search = searchTerm.trim().toLocaleLowerCase("zh-CN");
    return allVirtualIPs.filter((ip) => {
      const matchesSearch =
        !search ||
        [ip.name, resolveCreatorLabel(ip.creator), ...(ip.tags ?? [])]
          .join(" ")
          .toLocaleLowerCase("zh-CN")
          .includes(search);
      const matchesTags = selectedTags.every((tag) =>
        (ip.tags ?? []).includes(tag),
      );
      return matchesSearch && matchesTags;
    });
  }, [allVirtualIPs, searchTerm, selectedTags]);

  const allTags = useMemo(
    () => Array.from(new Set(allVirtualIPs.flatMap((ip) => ip.tags ?? []))),
    [allVirtualIPs],
  );

  const toggleTag = useCallback((tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  }, []);

  const deleteVirtualIPById = useCallback(
    async (bizId: string) => {
      try {
        const response = await virtualIPAPI.deleteVirtualIP(bizId);
        if (response.success) {
          setAllVirtualIPs((prev) =>
            prev.filter((ip) => ip.business_id !== bizId),
          );
        } else {
          showAlert({
            message: `删除失败: ${response.error || "未知错误"}`,
            variant: "error",
          });
        }
      } catch (error) {
        console.error("删除虚拟IP出错:", error);
        showAlert({ message: "删除失败，请重试", variant: "error" });
      }
    },
    [showAlert],
  );

  const handleDeleteIP = useCallback(
    (bizId: string) => {
      showAlert({
        title: "确认删除虚拟IP",
        message: "确定要删除这个虚拟IP吗？",
        variant: "warning",
        confirmText: "删除",
        onConfirm: () => {
          void deleteVirtualIPById(bizId);
        },
      });
    },
    [deleteVirtualIPById, showAlert],
  );

  const prependVirtualIP = useCallback((virtualIP: VirtualIP) => {
    setAllVirtualIPs((prev) => [virtualIP, ...prev]);
  }, []);

  return {
    virtualIPs,
    loading,
    searchTerm,
    setSearchTerm,
    selectedTags,
    toggleTag,
    allTags,
    handleDeleteIP,
    prependVirtualIP,
  };
}
