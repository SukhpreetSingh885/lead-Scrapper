"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { LocationSuggestion, LocationValidationResult } from "@/types";

export function useLocationSuggestions(query: string) {
  return useQuery<LocationSuggestion[]>({
    queryKey: ["locations-suggest", query],
    queryFn: () =>
      apiClient<LocationSuggestion[]>("/api/v1/locations", {
        params: { q: query, limit: 10 },
      }),
    enabled: query.length >= 1,
    staleTime: 60000,
  });
}

export function useValidateLocation(location: string) {
  return useQuery<LocationValidationResult>({
    queryKey: ["locations-validate", location],
    queryFn: () =>
      apiClient<LocationValidationResult>("/api/v1/locations/validate", {
        params: { location },
      }),
    enabled: location.trim().length >= 2,
    staleTime: 30000,
  });
}

