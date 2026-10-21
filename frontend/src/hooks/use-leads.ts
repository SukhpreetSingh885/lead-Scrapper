"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { LeadListItem, LeadBranchDetail, PaginatedResponse, DashboardMetrics } from "@/types";

export function useLeads(params: Record<string, any> = {}) {
  return useQuery<PaginatedResponse<LeadListItem>>({
    queryKey: ["leads", params],
    queryFn: () => apiClient<PaginatedResponse<LeadListItem>>("/api/v1/leads", { params }),
  });
}

export function useLeadDetail(leadId: string) {
  return useQuery<LeadBranchDetail>({
    queryKey: ["lead", leadId],
    queryFn: () => apiClient<LeadBranchDetail>(`/api/v1/leads/${leadId}`),
    enabled: Boolean(leadId),
  });
}

export function useDashboardMetrics() {
  return useQuery<DashboardMetrics>({
    queryKey: ["dashboard-metrics"],
    queryFn: () => apiClient<DashboardMetrics>("/api/v1/leads/metrics/dashboard"),
    refetchInterval: 10000,
  });
}

export function useEnrichLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (leadId: string) =>
      apiClient<{ success: boolean; pages_crawled: number; phones: number; emails: number; socials: number }>(
        `/api/v1/leads/${leadId}/enrich`,
        { method: "POST" }
      ),
    onSuccess: (_, leadId) => {
      queryClient.invalidateQueries({ queryKey: ["lead", leadId] });
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-metrics"] });
    },
  });
}

export function useUpdateLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ leadId, data }: { leadId: string; data: Record<string, any> }) =>
      apiClient<LeadBranchDetail>(`/api/v1/leads/${leadId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    onSuccess: (_, { leadId }) => {
      queryClient.invalidateQueries({ queryKey: ["lead", leadId] });
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-metrics"] });
    },
  });
}

export function useDeleteLead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (leadId: string) =>
      apiClient<{ message: string }>(`/api/v1/leads/${leadId}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-metrics"] });
    },
  });
}

export function useBulkDeleteLeads() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { lead_ids?: string[]; delete_all_filtered?: boolean; filters?: Record<string, any> }) =>
      apiClient<import("@/types").DeleteLeadsResponse>("/api/v1/leads/bulk-delete", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-metrics"] });
    },
  });
}

