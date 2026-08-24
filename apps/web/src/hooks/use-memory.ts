import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { LocatorMemory, EpisodeMemory, FailurePattern, SearchMemoryRequest, SearchMemoryResponse } from '@/types';

const MEMORY_KEY = 'memory';

export function useLocatorMemory(projectId: string) {
  return useQuery({
    queryKey: [MEMORY_KEY, 'locators', projectId],
    queryFn: () => api.get<LocatorMemory[]>(`/projects/${projectId}/memory/locators`),
    select: (response) => response.data,
    enabled: !!projectId,
  });
}

export function useEpisodeMemory(projectId: string) {
  return useQuery({
    queryKey: [MEMORY_KEY, 'episodes', projectId],
    queryFn: () => api.get<EpisodeMemory[]>(`/projects/${projectId}/memory/episodes`),
    select: (response) => response.data,
    enabled: !!projectId,
  });
}

export function useFailurePatterns(projectId: string) {
  return useQuery({
    queryKey: [MEMORY_KEY, 'failure-patterns', projectId],
    queryFn: () => api.get<FailurePattern[]>(`/projects/${projectId}/memory/failure-patterns`),
    select: (response) => response.data,
    enabled: !!projectId,
  });
}

export function useSearchMemory(projectId: string) {
  return useMutation({
    mutationFn: (data: SearchMemoryRequest) => api.post<SearchMemoryResponse>(`/projects/${projectId}/memory/search`, data),
  });
}