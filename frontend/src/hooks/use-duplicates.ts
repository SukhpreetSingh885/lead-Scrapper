"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { DuplicateCandidate, PaginatedResponse } from "@/types";

export function useDuplicateCandidates(page: number = 1, pageSize: number = 20) {
  return useQuery<PaginatedResponse<DuplicateCandidate>>({
    queryKey: ["duplicates", page, pageSize],
    queryFn: () =>
      apiClient<PaginatedResponse<DuplicateCandidate>>("/api/v1/duplicates", {
        params: { page, page_size: pageSize },
      }),
  });
}

export function useResolveDuplicate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      candidateId,
      resolution,
      notes,
    }: {
      candidateId: string;
      resolution: "merge" | "keep_distinct" | "reject_candidate";
      notes?: string;
    }) =>
      apiClient<{ message: string; success: boolean }>(
        `/api/v1/duplicates/${candidateId}/resolve`,
        {
          method: "POST",
          body: JSON.stringify({ resolution, notes }),
        }
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["duplicates"] });
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-metrics"] });
    },
  });
}

