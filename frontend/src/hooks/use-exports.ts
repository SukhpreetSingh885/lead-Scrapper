"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ExportItem } from "@/types";

export function useCreateExport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (exportData: {
      file_format: "csv" | "xlsx";
      selected_ids?: string[];
      city?: string;
      state?: string;
      category?: string;
      has_mobile?: boolean;
      has_email?: boolean;
    }) =>
      apiClient<ExportItem>("/api/v1/exports", {
        method: "POST",
        body: JSON.stringify(exportData),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exports"] });
    },
  });
}

export function useExportStatus(exportId?: string) {
  return useQuery<ExportItem>({
    queryKey: ["export-status", exportId],
    queryFn: () => apiClient<ExportItem>(`/api/v1/exports/${exportId}`),
    enabled: Boolean(exportId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ["pending", "processing"].includes(status) ? 1500 : false;
    },
  });
}

