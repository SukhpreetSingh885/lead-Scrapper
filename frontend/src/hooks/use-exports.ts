"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { ExportItem, IndustryExportOption } from "@/types";

export function useExportIndustries() {
  return useQuery<IndustryExportOption[]>({
    queryKey: ["export-industries"],
    queryFn: () => apiClient<IndustryExportOption[]>("/api/v1/exports/industries"),
    staleTime: 1000 * 30, // 30 seconds cache
  });
}

export function useCreateExport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (exportData: {
      file_format: "csv" | "xlsx";
      export_mode?: "single" | "all_combined" | "all_separate_zip";
      selected_ids?: string[];
      city?: string;
      state?: string;
      category?: string;
      job_id?: string;
      has_contact_number?: boolean;
      contact_qualified?: boolean;
      has_mobile?: boolean;
      has_email?: boolean;
    }) =>
      apiClient<ExportItem>("/api/v1/exports", {
        method: "POST",
        body: JSON.stringify(exportData),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exports"] });
      queryClient.invalidateQueries({ queryKey: ["export-industries"] });
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
