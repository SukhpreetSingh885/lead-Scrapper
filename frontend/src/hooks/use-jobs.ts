"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { DiscoveryJob, PaginatedResponse } from "@/types";

export function useDiscoveryJobs(page: number = 1, pageSize: number = 20) {
  return useQuery<PaginatedResponse<DiscoveryJob>>({
    queryKey: ["discovery-jobs", page, pageSize],
    queryFn: () =>
      apiClient<PaginatedResponse<DiscoveryJob>>("/api/v1/discovery/jobs", {
        params: { page, page_size: pageSize },
      }),
    refetchInterval: (query) => {
      // Auto-poll if any job is currently pending or running
      const hasRunning = query.state.data?.items.some((j) =>
        ["pending", "queued", "running"].includes(j.status)
      );
      return hasRunning ? 2000 : 15000;
    },
  });
}

export function useDiscoveryJob(jobId: string) {
  return useQuery<DiscoveryJob>({
    queryKey: ["discovery-job", jobId],
    queryFn: () => apiClient<DiscoveryJob>(`/api/v1/discovery/jobs/${jobId}`),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ["pending", "queued", "running"].includes(status) ? 2000 : false;
    },
  });
}

export function useCreateDiscoveryJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobData: {
      location: string;
      category: string;
      max_leads: number;
      source?: string;
      must_have_phone?: boolean;
      must_have_mobile?: boolean;
      must_have_email?: boolean;
      must_have_website?: boolean;
      must_have_whatsapp?: boolean;
      exclude_already_saved?: boolean;
    }) =>
      apiClient<DiscoveryJob>("/api/v1/discovery/jobs", {
        method: "POST",
        body: JSON.stringify(jobData),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["discovery-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-metrics"] });
    },
  });
}

